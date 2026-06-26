/**
 * sidebar-panels.ts — OpenCode TUI plugin
 *
 * Adds two collapsible sidebar sections:
 *   1. Spend  (order 105) — monthly + yearly token spend across all sessions
 *   2. Agents (order 150) — current active agent with live busy/idle indicator
 *
 * Uses only the public TuiPluginApi — no source build required.
 *
 * Module format: default export { id, tui } as required by readV1Plugin().
 */

import type { TuiPlugin, TuiPluginApi } from "@opencode-ai/plugin/tui"
import { createMemo, createSignal, createResource, Show } from "solid-js"

// ─── Spend Panel ─────────────────────────────────────────────────────────────

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

function SpendView(props: { api: TuiPluginApi }) {
  const theme = () => props.api.theme.current
  const [open, setOpen] = createSignal(true)

  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() // 0-indexed

  // Fetch all sessions via the REST client.
  // Re-fetches whenever the component re-mounts (session switch).
  const [sessions] = createResource(async () => {
    const res = await props.api.client.session.list({ limit: 1000 })
    return res.data ?? []
  })

  const thisMonthCost = createMemo(() =>
    (sessions() ?? []).reduce((sum, s) => {
      const d = new Date(s.time.created)
      if (d.getFullYear() === currentYear && d.getMonth() === currentMonth) {
        return sum + (s.cost ?? 0)
      }
      return sum
    }, 0),
  )

  const thisYearCost = createMemo(() =>
    (sessions() ?? []).reduce((sum, s) => {
      const d = new Date(s.time.created)
      if (d.getFullYear() === currentYear) {
        return sum + (s.cost ?? 0)
      }
      return sum
    }, 0),
  )

  // Hide until there is non-zero yearly spend
  const show = createMemo(() => !sessions.loading && thisYearCost() > 0)

  return (
    <Show when={show()}>
      <box>
        <box flexDirection="row" gap={1} onMouseDown={() => setOpen((x) => !x)}>
          <text fg={theme().text}>{open() ? "▼" : "▶"}</text>
          <text fg={theme().text}>
            <b>Spend</b>
            <Show when={!open()}>
              <span style={{ fg: theme().textMuted }}>
                {" "}({money.format(thisYearCost())} this year)
              </span>
            </Show>
          </text>
        </box>

        <Show when={open()}>
          <box
            flexDirection="row"
            justifyContent="space-between"
            paddingRight={1}
          >
            <text fg={theme().textMuted}>This month</text>
            <text fg={theme().text}>{money.format(thisMonthCost())}</text>
          </box>
          <box
            flexDirection="row"
            justifyContent="space-between"
            paddingRight={1}
          >
            <text fg={theme().textMuted}>This year</text>
            <text fg={theme().text}>{money.format(thisYearCost())}</text>
          </box>
        </Show>
      </box>
    </Show>
  )
}

// ─── Agent Monitor ───────────────────────────────────────────────────────────

const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

function useSpinner() {
  const [frame, setFrame] = createSignal(0)
  let interval: ReturnType<typeof setInterval> | undefined
  const start = () => {
    if (interval !== undefined) return
    interval = setInterval(
      () => setFrame((f) => (f + 1) % SPINNER_FRAMES.length),
      80,
    )
  }
  const stop = () => {
    if (interval === undefined) return
    clearInterval(interval)
    interval = undefined
    setFrame(0)
  }
  const char = () => SPINNER_FRAMES[frame()]!
  return { start, stop, char }
}

function AgentsView(props: { api: TuiPluginApi; session_id: string }) {
  const theme = () => props.api.theme.current
  const [open, setOpen] = createSignal(true)

  const session = createMemo(() => props.api.state.session.get(props.session_id))
  const status = createMemo(() =>
    props.api.state.session.status(props.session_id),
  )

  const agentName = createMemo(() => session()?.agent)
  const isBusy = createMemo(() => status()?.type === "busy")
  const isRetry = createMemo(() => status()?.type === "retry")
  const show = createMemo(() => !!agentName())

  const spinner = useSpinner()

  // Drive spinner from busy state
  createMemo(() => {
    if (isBusy()) spinner.start()
    else spinner.stop()
  })

  return (
    <Show when={show()}>
      <box>
        <box
          flexDirection="row"
          gap={1}
          onMouseDown={() => setOpen((x) => !x)}
        >
          <text fg={theme().text}>{open() ? "▼" : "▶"}</text>
          <text fg={theme().text}>
            <b>Agent</b>
            <Show when={!open()}>
              <span style={{ fg: theme().textMuted }}>
                {" "}({agentName()})
              </span>
            </Show>
          </text>
        </box>

        <Show when={open()}>
          <box flexDirection="row" gap={1} alignItems="flex-start">
            {/* Status indicator */}
            <box flexShrink={0} width={1}>
              <Show
                when={isBusy()}
                fallback={
                  <text fg={isRetry() ? theme().warning : theme().text}>
                    {isRetry() ? "!" : "●"}
                  </text>
                }
              >
                <text fg={theme().accent}>{spinner.char()}</text>
              </Show>
            </box>

            {/* Agent name + state label */}
            <text fg={theme().text} wrapMode="word">
              {agentName()}
              <Show when={isBusy()}>
                <span style={{ fg: theme().textMuted }}> working</span>
              </Show>
              <Show when={isRetry()}>
                <span style={{ fg: theme().warning }}> retrying</span>
              </Show>
              <Show when={!isBusy() && !isRetry()}>
                <span style={{ fg: theme().textMuted }}> idle</span>
              </Show>
            </text>
          </box>
        </Show>
      </box>
    </Show>
  )
}

// ─── Plugin registration ──────────────────────────────────────────────────────

const tui: TuiPlugin = async (api) => {
  api.slots.register({
    order: 105,
    slots: {
      sidebar_content() {
        return <SpendView api={api} />
      },
    },
  })

  api.slots.register({
    order: 150,
    slots: {
      sidebar_content(_ctx, props) {
        return <AgentsView api={api} session_id={props.session_id} />
      },
    },
  })
}

export default {
  id: "local:sidebar-panels",
  tui,
}
