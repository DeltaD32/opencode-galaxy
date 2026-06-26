#!/usr/bin/env python3
"""
video_pipeline.py
=================
Orchestrator — converts a .txt file into a fully rendered .mp4 video.

Pipeline steps:
  1. Structure dialogue & plan visuals        (dialogue.py)
  2. Generate TTS narration                   (tts.py)
  3. Distribute TTS durations                 (tts.py)
  4. Transcribe audio → SRT subtitles        (transcription.py)
  5. Render per-segment visuals + attach TTS  (manim_renderer.py / image_generator.py)
       → slice TTS audio per segment
       → mux audio slice into each segment clip
       → concatenate muxed clips
  6. Write combined video to output path

Usage:
    python video_pipeline.py input.txt -o output_video.mp4 [--high-quality]

Required environment variables (or .env file):
    BMW_CLIENT_ID      OAuth client ID
    BMW_CLIENT_SECRET  OAuth client secret
    BMW_API_KEY        x-apikey value for APIM gateway

Optional:
    BMW_ENV            'int' or 'prod' (default: prod)
    BMW_CHAT_MODEL     chat model ID (default: gpt-5)
    BMW_MANIM_MODEL    code-gen model (default: anthropic/claude-sonnet-4)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# .env bootstrap
# ---------------------------------------------------------------------------

_REQUIRED_VARS = ["BMW_CLIENT_ID", "BMW_CLIENT_SECRET", "BMW_API_KEY"]


def _ensure_env_file() -> None:
    """If no .env exists and required env vars are missing, prompt the user
    interactively to enter them and write a .env file at the repo root."""
    # Repo root is one level above scripts/
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"

    # If .env already exists, (re-)load it and return
    if env_file.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(dotenv_path=env_file, override=False)
        except ImportError:
            pass
        return

    # Check whether all required vars are already present in the environment
    missing = [v for v in _REQUIRED_VARS if not os.environ.get(v, "").strip()]
    if not missing:
        return

    print(
        "\n[setup] No .env file found and the following required environment "
        "variables are missing:\n"
        + "\n".join(f"  • {v}" for v in missing)
        + "\n\nPlease enter their values now — they will be saved to:\n"
        f"  {env_file}\n"
    )

    values: dict[str, str] = {}
    for var in _REQUIRED_VARS:
        existing = os.environ.get(var, "").strip()
        if existing:
            values[var] = existing
            continue
        while True:
            val = input(f"  {var}: ").strip()
            if val:
                values[var] = val
                break
            print(f"    [!] {var} cannot be empty. Please try again.")

    env_file.write_text(
        "".join(f"{k}={v}\n" for k, v in values.items()),
        encoding="utf-8",
    )
    print(f"\n[setup] .env written to {env_file}\n")

    # Load into the current process so the rest of the pipeline sees the values
    for k, v in values.items():
        os.environ[k] = v


# ---------------------------------------------------------------------------
# Module imports
# ---------------------------------------------------------------------------
from bmw_client import bmw_setup  # noqa: E402
from character_planner import inject_character_descriptions, plan_characters  # noqa: E402
from dialogue import CHAT_MODEL, structure_dialogue, summarise_to_duration  # noqa: E402
from image_generator import render_image_segment  # noqa: E402
from manim_renderer import render_manim_segment  # noqa: E402
from slide_planner import plan_slide_dialogue  # noqa: E402
from slide_renderer import render_slide_segment  # noqa: E402
from storyboard_planner import get_segment_hint, plan_visual_style  # noqa: E402
from transcription import (  # noqa: E402
    generate_srt,
    get_segment_cards,
    get_segment_words,
    transcribe_audio,
)
from tts import (  # noqa: E402
    apply_tts_durations,
    generate_tts_audio,
    generate_tts_slide_narration,
    get_audio_duration,
)

MANIM_MODEL = os.environ.get("BMW_MANIM_MODEL", "anthropic/claude-sonnet-4-6")
MAX_PARALLEL_MANIM = 5
TARGET_VIDEO_WIDTH = 1280
TARGET_VIDEO_HEIGHT = 720


# ---------------------------------------------------------------------------
# Input reader
# ---------------------------------------------------------------------------


def read_input_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        sys.exit(f"[ERROR] Input file not found: {filepath}")
    if path.suffix.lower() != ".txt":
        sys.exit(f"[ERROR] Expected a .txt file, got: {path.suffix}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Visual segment rendering dispatcher
# ---------------------------------------------------------------------------


def _render_one_segment(
    idx: int,
    n: int,
    seg: dict,
    segments: list[dict],
    video_title: str,
    style_guide: dict,
    client,
    work_dir: Path,
    high_quality: bool,
    api_key: str,
    token: str,
    base_url: str,
    ca_cert: str,
    language: str = "en",
) -> tuple:
    """Render a single segment. Returns (idx, clip_path, status_message)."""
    vtype = seg.get("visual_type", "manim").lower()
    duration = float(seg.get("duration_seconds", 5))
    seg_id = seg.get("id", idx + 1)
    label = seg.get("speaker_text", "")[:50]
    print(f"  [seg {idx + 1}/{n}] type={vtype}  dur={duration}s  — {label}…")

    prev_segment = segments[idx - 1] if idx > 0 else None
    next_segment = segments[idx + 1] if idx < len(segments) - 1 else None
    segment_hint = get_segment_hint(style_guide, seg_id)

    if vtype == "image":
        try:
            clip_path = render_image_segment(seg, work_dir, api_key, token, base_url, ca_cert)
            return (idx, clip_path, "image generated OK")
        except BaseException as exc:
            print(
                f"  [WARN] Image generation failed for seg {seg_id}: {exc}\n         Falling back to Manim."
            )
            vtype = "manim"

    clip_path = render_manim_segment(
        client,
        seg,
        work_dir,
        high_quality,
        seg_id,
        manim_model=MANIM_MODEL,
        segment_index=idx,
        total_segments=n,
        video_title=video_title,
        prev_segment=prev_segment,
        next_segment=next_segment,
        style_guide=style_guide,
        segment_hint=segment_hint,
        language=language,
    )
    return (idx, clip_path, "manim rendered OK")


def _attach_segment_audio(
    clip_paths: list[Path],
    segments: list[dict],
    audio_file: Path,
    work_dir: Path,
) -> list[Path]:
    """Slice the full TTS audio per segment and mux each slice into its video clip.

    Each segment's audio window is determined by the cumulative sum of
    ``duration_seconds`` values already set by ``apply_tts_durations``.
    Uses ffmpeg directly (subprocess) to avoid MoviePy audio-reader instability.
    """
    import subprocess

    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    muxed_paths: list[Path] = []
    cursor = 0.0

    for idx, (clip_path, seg) in enumerate(zip(clip_paths, segments)):
        seg_dur = float(seg.get("duration_seconds", 0))
        audio_start = cursor
        audio_end = cursor + seg_dur
        cursor += seg_dur

        muxed_path = work_dir / f"seg_{idx + 1:03d}_muxed.mp4"
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i",
            str(clip_path),
            "-ss",
            str(audio_start),
            "-to",
            str(audio_end),
            "-i",
            str(audio_file),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            str(muxed_path),
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg mux failed for segment {idx + 1}:\n"
                + result.stderr.decode(errors="replace")
            )
        muxed_paths.append(muxed_path)

    return muxed_paths


def _normalize_clip_resolution(
    clip_path: Path,
    work_dir: Path,
    clip_index: int,
    target_width: int = TARGET_VIDEO_WIDTH,
    target_height: int = TARGET_VIDEO_HEIGHT,
) -> Path:
    """Resize and center-crop a clip to the target 16:9 canvas."""
    from moviepy.editor import VideoFileClip
    from moviepy.video.fx.all import crop

    clip = VideoFileClip(str(clip_path))
    try:
        if clip.w == target_width and clip.h == target_height:
            return clip_path

        scale = max(target_width / clip.w, target_height / clip.h)
        fitted = clip.resize(scale)
        normalized = crop(
            fitted,
            width=target_width,
            height=target_height,
            x_center=fitted.w / 2,
            y_center=fitted.h / 2,
        )
        out_path = work_dir / f"seg_{clip_index + 1:03d}_720p.mp4"
        normalized.write_videofile(
            str(out_path),
            fps=clip.fps or 24,
            codec="libx264",
            audio=False,
            logger=None,
        )
        normalized.close()
        fitted.close()
        return out_path
    finally:
        clip.close()


def render_segment_visuals(
    client,
    script: dict,
    work_dir: Path,
    high_quality: bool,
    api_key: str,
    token: str,
    base_url: str,
    ca_cert: str,
    audio_file: Path,
    language: str = "en",
) -> Path:
    """Render segments in parallel (≤ MAX_PARALLEL_MANIM workers), attach the
    per-segment TTS audio slice to each clip, then concatenate into one MP4."""
    from moviepy.editor import VideoFileClip, concatenate_videoclips

    segments = script.get("segments", [])
    n = len(segments)
    video_title = script.get("title", "")
    style_guide = script.get("style_guide", {})
    results: dict[int, Path] = {}

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_MANIM) as pool:
        futures = {
            pool.submit(
                _render_one_segment,
                idx,
                n,
                seg,
                segments,
                video_title,
                style_guide,
                client,
                work_dir,
                high_quality,
                api_key,
                token,
                base_url,
                ca_cert,
                language,
            ): idx
            for idx, seg in enumerate(segments)
        }
        for future in as_completed(futures):
            idx = futures[future]
            seg_id = segments[idx].get("id", idx + 1)
            try:
                _, clip_path, status = future.result()
                results[idx] = clip_path
                print(f"         {status}")
            except RuntimeError as exc:
                sys.exit(f"[ERROR] Manim failed for segment {seg_id} after retries:\n{exc}")

    if not results:
        sys.exit("[ERROR] No segment clips were produced.")

    # Reassemble in original segment order and normalize to the 720p canvas
    clip_paths = [results[i] for i in range(n)]
    print(
        f"[5/6] Normalizing {len(clip_paths)} segment(s) to {TARGET_VIDEO_WIDTH}x{TARGET_VIDEO_HEIGHT} …"
    )
    clip_paths = [
        _normalize_clip_resolution(path, work_dir, idx) for idx, path in enumerate(clip_paths)
    ]

    # Attach each segment's TTS audio slice before concatenation
    print(f"[5/6] Attaching audio slices to {len(clip_paths)} segment(s) …")
    muxed_paths = _attach_segment_audio(clip_paths, segments, audio_file, work_dir)

    print(f"[5/6] Concatenating {len(muxed_paths)} muxed clip(s) …")
    if len(muxed_paths) == 1:
        return muxed_paths[0]

    clips = [VideoFileClip(str(p)) for p in muxed_paths]
    combined_video = work_dir / "combined.mp4"
    combined = concatenate_videoclips(clips, method="compose")
    combined.write_videofile(str(combined_video), codec="libx264", audio_codec="aac", logger=None)
    for c in clips:
        c.close()
    combined.close()
    return combined_video


# ---------------------------------------------------------------------------
# Slide pipeline
# ---------------------------------------------------------------------------


def _run_slide_pipeline(args, client, api_key, base_url, ca_cert, token, output_path: Path) -> None:
    """End-to-end pipeline for --mode slide.

    1. Plan narrator script + BMW slide specs
    2. Generate single-voice TTS (one MP3 per segment)
    3. Render each segment as a BMW HTML slide screenshot → MP4 clip
    4. Mux per-segment audio into each clip
    5. Concatenate and write final MP4
    """
    import subprocess as _sp

    import imageio_ffmpeg as _ffmpeg
    from moviepy.editor import VideoFileClip, concatenate_videoclips

    ffmpeg_exe = _ffmpeg.get_ffmpeg_exe()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # 1 — Read input and plan dialogue
        raw_text = read_input_file(args.input_file)

        # Condense text to target duration if requested
        if args.duration is not None:
            raw_text = summarise_to_duration(
                client,
                raw_text,
                target_minutes=args.duration,
                language=args.language,
            )

        script = plan_slide_dialogue(
            client,
            raw_text,
            language=args.language,
            summarise=args.summarize,
            target_duration=args.duration,
        )
        segments = script.get("segments", [])
        n = len(segments)

        # 2 — Generate per-segment TTS (single narrator)
        audio_paths = generate_tts_slide_narration(
            script,
            tmp,
            api_key,
            token,
            base_url,
            ca_cert,
            language=args.language,
        )

        # 3 — Render each segment as a BMW slide clip
        print(f"[3/6] Rendering {n} BMW slide(s) …")
        clip_paths: list[Path] = []
        for idx, seg in enumerate(segments):
            _seg_id = seg.get("id", idx + 1)
            speaker = seg.get("speaker", "narrator").upper()
            label = seg.get("speaker_text", "")[:50]
            print(
                f"  [slide {idx + 1}/{n}] speaker={speaker}  dur={seg['duration_seconds']}s  — {label}…"
            )
            clip_path = render_slide_segment(seg, tmp, total_slides=n)
            clip_paths.append(clip_path)
            print("         slide rendered OK")

        # 4 — Mux per-segment audio into each clip
        print(f"[4/6] Muxing audio into {n} slide clip(s) …")
        muxed_paths: list[Path] = []
        for idx, (clip_path, seg, audio_path) in enumerate(zip(clip_paths, segments, audio_paths)):
            muxed_path = tmp / f"seg_{idx + 1:03d}_muxed.mp4"
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i",
                str(clip_path),
                "-i",
                str(audio_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-shortest",
                str(muxed_path),
            ]
            result = _sp.run(cmd, capture_output=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg mux failed for slide {idx + 1}:\n"
                    + result.stderr.decode(errors="replace")
                )
            muxed_paths.append(muxed_path)

        # 5 — Concatenate and write output
        print(f"[5/6] Concatenating {len(muxed_paths)} muxed clip(s) …")
        if len(muxed_paths) == 1:
            combined_video = muxed_paths[0]
        else:
            clips = [VideoFileClip(str(p)) for p in muxed_paths]
            combined_video = tmp / "combined.mp4"
            combined = concatenate_videoclips(clips, method="compose")
            combined.write_videofile(
                str(combined_video), codec="libx264", audio_codec="aac", logger=None
            )
            for c in clips:
                c.close()
            combined.close()

        print("[6/6] Writing output …")
        shutil.copy2(str(combined_video), str(output_path))

    resolved = output_path.resolve()
    size_mb = resolved.stat().st_size / (1024 * 1024)
    print(f"\nVideo ready: {resolved}  ({size_mb:.1f} MB)")
    _notify(resolved, size_mb)


# ---------------------------------------------------------------------------
# macOS notification
# ---------------------------------------------------------------------------


def _notify(resolved: "Path", size_mb: float) -> None:
    """Fire a clickable macOS notification via terminal-notifier (if installed).

    Clicking the banner opens the rendered video in the default player.
    The subtitle shows the full path so the user knows exactly where the file lives.
    Silently does nothing if terminal-notifier is not on PATH.
    """
    import shutil as _shutil
    import subprocess as _sp

    tn = _shutil.which("terminal-notifier")
    if not tn:
        return

    file_url = resolved.as_uri()  # file:///Users/…/ClipJointVideos/mcp_explainer.mp4
    rel_path = f"~/Documents/ClipJointVideos/{resolved.name}"

    _sp.run(
        [
            tn,
            "-title",    "🎬 ClipJoint — Video Ready",
            "-subtitle", f"{resolved.name}  ·  {size_mb:.1f} MB",
            "-message",  rel_path,
            "-sound",    "Glass",
            "-open",     file_url,   # click → opens in default video player
        ],
        check=False,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Generate an MP4 video from a .txt file using {CHAT_MODEL}, Manim, and BMW TTS."
    )
    parser.add_argument("input_file", help="Path to the input .txt file")
    _default_output_dir = Path.home() / "Documents" / "ClipJointVideos"
    _default_output = str(_default_output_dir / "output_video.mp4")
    parser.add_argument(
        "-o",
        "--output",
        default=_default_output,
        help=f"Output .mp4 file path (default: {_default_output})",
    )
    parser.add_argument(
        "--high-quality",
        action="store_true",
        help="Render Manim in high quality (-qh). Slower but sharper.",
    )
    parser.add_argument(
        "--visual-mode",
        choices=["mix", "images", "diagrams"],
        default="mix",
        help=(
            "Visual style for the video: "
            "'mix' (default) — let the AI choose images or diagrams per segment; "
            "'images' — every segment uses an AI-generated image; "
            "'diagrams' — every segment uses a Manim animated diagram."
        ),
    )
    parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help=(
            "Language for narration and diagram labels: "
            "'en' (default) — English; "
            "'de' — German (TTS voice, diagram labels, and visual planner all switch to German)."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["standard", "slide"],
        default="standard",
        help=(
            "Pipeline mode: "
            "'standard' (default) — Manim + AI images with single narrator; "
            "'slide' — BMW-branded HTML slides with single narrator voice."
        ),
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        default=False,
        help=(
            "(slide mode) Compress the input text to a concise 4–8 exchange "
            "deep-dive. By default, summarisation is OFF and the full input "
            "text is used."
        ),
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        metavar="MINUTES",
        help=(
            "Approximate target duration for the video in minutes (optional). "
            "When set, the pipeline condenses or expands content to fit. "
            "If omitted, duration is determined by the input text length."
        ),
    )
    args = parser.parse_args()

    _ensure_env_file()
    client, api_key, base_url, ca_cert, token = bmw_setup()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "slide":
        _run_slide_pipeline(args, client, api_key, base_url, ca_cert, token, output_path)
        return

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # 1 — Read input and structure into segments
        raw_text = read_input_file(args.input_file)

        # Condense text to target duration if requested
        if args.duration is not None:
            raw_text = summarise_to_duration(
                client,
                raw_text,
                target_minutes=args.duration,
                language=args.language,
            )

        script = structure_dialogue(
            client, raw_text, visual_mode=args.visual_mode, language=args.language
        )
        segments = script.get("segments", [])
        manim_count = sum(1 for s in segments if s.get("visual_type", "manim") == "manim")
        image_count = len(segments) - manim_count
        print(
            f"     Title    : {script.get('title', 'N/A')}\n"
            f"     Duration : ~{script.get('estimated_duration_seconds', '?')}s\n"
            f"     Segments : {len(segments)}  (manim: {manim_count}, image: {image_count})"
        )

        # Steps 1.5 + 1.6 + 2 — run concurrently via asyncio.gather + asyncio.to_thread
        #
        # Dependency graph after structure_dialogue():
        #   plan_characters    — needs script only (sync, CPU+LLM)
        #   plan_visual_style  — needs script only (sync, CPU+LLM)
        #   generate_tts_audio — needs script only (sync, HTTP)
        #
        # All three are independent of each other, so we fire them in parallel.
        # asyncio.to_thread() runs each blocking call in a thread-pool worker
        # without blocking the event loop, giving us true I/O concurrency
        # with no changes to the individual module APIs.
        import asyncio

        async def _parallel_prep():
            tasks = []

            if image_count > 0:
                print("[1.5/7] Planning character consistency …  (parallel)")
                tasks.append(
                    asyncio.to_thread(plan_characters, client, script, language=args.language)
                )
            else:
                tasks.append(asyncio.sleep(0, result={}))  # no-op placeholder

            print("[1.6/7] Planning visual storyboard …  (parallel)")
            tasks.append(
                asyncio.to_thread(plan_visual_style, client, script, manim_model=MANIM_MODEL)
            )

            print("[2/7]   Generating TTS audio …  (parallel)")
            tasks.append(
                asyncio.to_thread(
                    generate_tts_audio,
                    script,
                    tmp,
                    api_key,
                    token,
                    base_url,
                    ca_cert,
                    step_label="2/7",
                    language=args.language,
                )
            )

            return await asyncio.gather(*tasks)

        char_result, style_result, audio_file = asyncio.run(_parallel_prep())

        character_registry = char_result if image_count > 0 else {}
        if image_count > 0:
            inject_character_descriptions(script, character_registry)

        style_guide = style_result
        script["style_guide"] = style_guide

        # 3 — Update segment durations from actual TTS audio duration
        print("[3/7] Updating segment durations from TTS audio …")
        apply_tts_durations(script, audio_file)

        # 4 — Transcribe audio → word-level timings before Manim so each segment
        #     receives exact per-word timestamps for animation synchronisation.
        word_timings = transcribe_audio(
            audio_file,
            api_key,
            token,
            base_url,
            ca_cert,
            total_duration=get_audio_duration(audio_file),
        )
        if word_timings:
            srt_path = output_path.with_suffix(".srt")
            generate_srt(word_timings, srt_path)
            print(f"     SRT saved  : {srt_path}")
            # Attach word_timings (relative to segment start) to each segment dict.
            # Manim uses these to know the exact second at which to draw each element.
            cursor = 0.0
            for seg in script.get("segments", []):
                seg_dur = float(seg.get("duration_seconds", 0))
                seg["word_timings"] = get_segment_words(word_timings, cursor, cursor + seg_dur)
                seg["subtitle_cards"] = get_segment_cards(word_timings, cursor, cursor + seg_dur)
                cursor += seg_dur
        else:
            print("     [WARN] No transcript; animation timing will be evenly distributed.")

        # 5 — Render per-segment visuals, attach per-segment TTS audio slices,
        #     then concatenate the muxed clips into the final video
        print(f"[5/7] Rendering {len(script.get('segments', []))} segment(s) …")
        combined_video = render_segment_visuals(
            client,
            script,
            tmp,
            args.high_quality,
            api_key,
            token,
            base_url,
            ca_cert,
            audio_file=audio_file,
            language=args.language,
        )

        # 6 — Copy the combined (audio + video) file to the requested output path
        print("[6/7] Writing output …")
        shutil.copy2(str(combined_video), str(output_path))

    resolved = output_path.resolve()
    size_mb = resolved.stat().st_size / (1024 * 1024)
    print(f"\nVideo ready: {resolved}  ({size_mb:.1f} MB)")
    _notify(resolved, size_mb)


if __name__ == "__main__":
    main()
