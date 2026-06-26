#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "Pillow",
# ]
# ///

"""
download_assets.py - Robust asset downloader for bmw-html.

Input manifest format (JSON):
[
  {
    "slide": 1,
    "type": "background",
    "file": "title_bg.jpg",
    "url": "https://...",
    "source": "Unsplash / @name",
    "license": "Unsplash License",
    "attribution": "Photo by Name on Unsplash"
  }
]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download deck assets with retries.")
    parser.add_argument("--manifest", required=True, help="Path to JSON manifest file.")
    parser.add_argument("--assets-dir", required=True, help="Output folder for assets.")
    parser.add_argument(
        "--output-manifest",
        default="",
        help="Optional path for resolved manifest JSON with status/local_path.",
    )
    parser.add_argument("--retries", type=int, default=3, help="Retries per asset (default: 3).")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--convert-jpg",
        action="store_true",
        help="Convert non-JPG images to JPG (quality=85).",
    )
    parser.add_argument(
        "--require-slides",
        default="",
        help="Comma-separated required slide numbers. Script fails if any required slide download fails/missing.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("Manifest must be a JSON list.")
    for i, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Manifest item {i} is not an object.")
        if "file" not in item:
            raise ValueError(f"Manifest item {i} must include 'file'.")
        if "url" not in item and "page_url" not in item:
            raise ValueError(f"Manifest item {i} must include 'url' or 'page_url'.")
    return payload


def _parse_required_slides(raw: str) -> set[int]:
    if not raw.strip():
        return set()
    out = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            out.add(int(part))
    return out


def _provider_from(item: dict, url: str) -> str:
    source = str(item.get("source", "")).lower()
    host = urllib.parse.urlsplit(url).netloc.lower()
    if "unsplash" in source or "unsplash" in host:
        return "unsplash"
    if "pexels" in source or "pexels" in host:
        return "pexels"
    if "pixabay" in source or "pixabay" in host:
        return "pixabay"
    if "wikimedia" in source or "wikipedia" in source or "wikimedia" in host:
        return "wikimedia"
    return "generic"


def _is_allowed_direct_image_url(url: str) -> tuple[bool, str]:
    p = urllib.parse.urlsplit(url)
    host = p.netloc.lower()
    path = p.path.lower()

    if p.scheme == "file":
        return True, ""

    if host == "source.unsplash.com":
        return False, "blocked_url_pattern:source.unsplash.com"

    # Unsplash photo page URLs are not direct binaries; resolve first.
    if host.endswith("unsplash.com") and "/photos/" in path and "/download" not in path:
        return False, "unsplash_page_url_needs_resolution"

    # Strong allow list for known binary hosts.
    if host.startswith("images.unsplash.com"):
        return True, ""
    if host.startswith("images.pexels.com"):
        return True, ""
    if host.endswith("pixabay.com") and "/photo/" in path:
        return True, ""
    if host.startswith("upload.wikimedia.org"):
        return True, ""

    # Generic fallback: allow and verify by preflight content-type.
    return True, ""


def _fetch_html(url: str, timeout: int) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (bmw-html asset resolver)",
            "Accept": "text/html,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read(600_000)
    return data.decode("utf-8", errors="ignore")


def _extract_og_image(html: str) -> str | None:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _resolve_candidate_url(url: str, timeout: int) -> str:
    p = urllib.parse.urlsplit(url)
    host = p.netloc.lower()
    path = p.path

    if p.scheme == "file":
        return url

    if host == "source.unsplash.com":
        raise ValueError("blocked_url_pattern:source.unsplash.com")

    if host.endswith("unsplash.com") and "/photos/" in path and "/download" not in path:
        # Prefer resolving to og:image (images.unsplash.com), fallback to /download endpoint.
        try:
            html = _fetch_html(url, timeout=timeout)
            og = _extract_og_image(html)
            if og:
                return og
        except Exception:
            pass
        if path.endswith("/"):
            dpath = path + "download"
        else:
            dpath = path + "/download"
        return urllib.parse.urlunsplit((p.scheme, p.netloc, dpath, "force=true&w=1920", ""))

    if host.endswith("wikimedia.org") and host != "upload.wikimedia.org" and "/wiki/File:" in path:
        # Try resolving wiki page to direct upload URL via og:image.
        html = _fetch_html(url, timeout=timeout)
        og = _extract_og_image(html)
        if og:
            return og

    return url


def _sniff_image_magic(chunk: bytes) -> bool:
    if chunk.startswith(b"\xff\xd8\xff"):  # jpeg
        return True
    if chunk.startswith(b"\x89PNG\r\n\x1a\n"):  # png
        return True
    if chunk.startswith(b"GIF87a") or chunk.startswith(b"GIF89a"):  # gif
        return True
    if len(chunk) >= 12 and chunk[:4] == b"RIFF" and chunk[8:12] == b"WEBP":
        return True
    return False


def _preflight_url(url: str, timeout: int) -> tuple[str, str, int]:
    p = urllib.parse.urlsplit(url)
    if p.scheme == "file":
        local = Path(urllib.request.url2pathname(p.path))
        if not local.exists():
            raise RuntimeError(f"preflight_failed:file_not_found:{local}")
        ctype = mimetypes.guess_type(str(local))[0] or ""
        if not ctype.startswith("image/"):
            raise RuntimeError(f"preflight_failed:not_image_content_type:{ctype or 'unknown'}")
        return url, ctype, 200

    # Try HEAD first.
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={
                "User-Agent": "Mozilla/5.0 (bmw-html asset preflight)",
                "Accept": "image/*,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            status = getattr(resp, "status", 200)
            final_url = resp.geturl()
            if ctype.startswith("image/"):
                return final_url, ctype, status
    except Exception:
        pass

    # Fallback: GET first bytes.
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (bmw-html asset preflight)",
            "Accept": "image/*,*/*;q=0.8",
            "Range": "bytes=0-8191",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        status = getattr(resp, "status", 200)
        final_url = resp.geturl()
        chunk = resp.read(8192)
        if ctype.startswith("image/") or _sniff_image_magic(chunk):
            return final_url, ctype, status
    raise RuntimeError("preflight_failed:not_an_image")


def _download_to_path(url: str, out_path: Path, timeout: int, retries: int) -> tuple[str, str, int]:
    last_err: Exception | None = None

    p = urllib.parse.urlsplit(url)
    if p.scheme == "file":
        src = Path(urllib.request.url2pathname(p.path))
        if not src.exists():
            raise RuntimeError(f"file_not_found:{src}")
        shutil.copyfile(src, out_path)
        ctype = mimetypes.guess_type(str(src))[0] or ""
        return url, ctype, 200

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (bmw-html asset downloader)",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                status = getattr(resp, "status", 200)
                final_url = resp.geturl()
                with NamedTemporaryFile(delete=False, dir=str(out_path.parent)) as tmp:
                    tmp.write(resp.read())
                    temp_name = tmp.name
            os.replace(temp_name, out_path)
            if ctype and not ctype.startswith("image/"):
                raise RuntimeError(f"downloaded_non_image_content_type:{ctype}")
            return final_url, ctype, status
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
            last_err = err
            if attempt < retries:
                time.sleep(1.5 * attempt)
            else:
                break
    raise RuntimeError(f"Download failed after {retries} attempts: {url}") from last_err


def _to_jpg(path: Path) -> Path:
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return path
    jpg_path = path.with_suffix(".jpg")
    with Image.open(path) as img:
        img.convert("RGB").save(jpg_path, "JPEG", quality=85, optimize=True)
    path.unlink(missing_ok=True)
    return jpg_path


def run() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    assets_dir = Path(args.assets_dir).expanduser().resolve()
    assets_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(manifest_path)
    required_slides = _parse_required_slides(args.require_slides)
    results: list[dict] = []

    print(f"Manifest: {manifest_path}")
    print(f"Assets : {assets_dir}")
    print("")

    for item in manifest:
        file_name = Path(str(item["file"])).name
        target = assets_dir / file_name

        entry = dict(item)
        entry["local_path"] = str(target)
        entry["provider"] = _provider_from(item, str(item.get("url") or item.get("page_url") or ""))

        try:
            # Fast-path: if file is already present, do not re-hit network.
            if target.exists():
                entry["status"] = "exists"
                print(f"[exists] {target.name}")
                if args.convert_jpg:
                    converted = _to_jpg(target)
                    if converted != target:
                        entry["file"] = converted.name
                        entry["local_path"] = str(converted)
                        print(f"[conv]   {target.name} -> {converted.name}")
                results.append(entry)
                continue

            primary_url = str(item.get("url") or item.get("page_url") or "")
            fallback_urls = [str(u) for u in item.get("fallback_urls", []) if str(u).strip()]
            candidates = [primary_url] + fallback_urls
            selected_url = ""
            preflight_ctype = ""
            preflight_status = 0
            last_resolve_err = None

            for candidate in candidates:
                resolved = _resolve_candidate_url(candidate, timeout=args.timeout)
                allowed, reason = _is_allowed_direct_image_url(resolved)
                if not allowed:
                    last_resolve_err = RuntimeError(reason)
                    continue
                try:
                    final_url, preflight_ctype, preflight_status = _preflight_url(
                        resolved, timeout=args.timeout
                    )
                    selected_url = final_url
                    entry["resolved_url"] = final_url
                    entry["preflight_status"] = preflight_status
                    entry["preflight_content_type"] = preflight_ctype
                    break
                except Exception as err:
                    last_resolve_err = err

            if not selected_url:
                raise RuntimeError(
                    f"no_valid_asset_url:{last_resolve_err or 'all candidates rejected'}"
                )

            final_url, ctype, status = _download_to_path(
                selected_url, target, timeout=args.timeout, retries=args.retries
            )
            entry["final_url"] = final_url
            entry["download_status_code"] = status
            entry["download_content_type"] = ctype
            entry["status"] = "downloaded"
            print(f"[ok]     {target.name}")

            if args.convert_jpg:
                converted = _to_jpg(target)
                if converted != target:
                    entry["file"] = converted.name
                    entry["local_path"] = str(converted)
                    print(f"[conv]   {target.name} -> {converted.name}")
        except Exception as err:  # noqa: BLE001 - keep robust and continue
            entry["status"] = "failed"
            entry["error"] = str(err)
            print(f"[fail]   {target.name}: {err}")

        results.append(entry)

    failed = sum(1 for r in results if r.get("status") == "failed")
    by_slide = {int(r.get("slide")): r for r in results if str(r.get("slide", "")).isdigit()}
    required_failed = []
    required_missing = []
    for s in sorted(required_slides):
        r = by_slide.get(s)
        if r is None:
            required_missing.append(s)
            continue
        if r.get("status") == "failed":
            required_failed.append(s)

    print("")
    print(f"Done. total={len(results)} failed={failed}")
    if required_slides:
        print(
            f"Required slides check: required={sorted(required_slides)} "
            f"failed={required_failed} missing={required_missing}"
        )

    if args.output_manifest:
        out_path = Path(args.output_manifest).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Resolved manifest: {out_path}")

    if required_failed or required_missing:
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
