// Running cost tracker — session total, estimated daily, monthly projection.
import type { Session } from "../types/opencode";

interface Props {
  sessions: Session[];
  activeSession?: Session;
}

function formatCost(n: number, decimals = 4): string {
  if (n === 0) return "$0.00";
  if (n < 0.0001) return "<$0.0001";
  return `$${n.toFixed(decimals)}`;
}

interface CostRowProps {
  label: string;
  value: string;
  highlight?: boolean;
  subtext?: string;
}

function CostRow({ label, value, highlight = false, subtext }: CostRowProps) {
  return (
    <div className="flex items-center justify-between py-2 px-3">
      <div>
        <p className="text-xs text-bmw-grey">{label}</p>
        {subtext && <p className="text-[10px] text-bmw-grey/40 mt-0.5">{subtext}</p>}
      </div>
      <p className={`text-xs font-medium tabular-nums ${highlight ? "text-bmw-blue-light" : "text-white/80"}`}>
        {value}
      </p>
    </div>
  );
}

export function CostTracker({ sessions, activeSession }: Props) {
  const totalAllTime = sessions.reduce((s, sess) => s + (sess.cost ?? 0), 0);
  const activeCost = activeSession?.cost ?? 0;

  // Naive daily / monthly estimate: based on average session cost × sessions today/month
  // We use session.time.updated to identify today's sessions
  const now = Date.now();
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const monthStart = new Date();
  monthStart.setDate(1);
  monthStart.setHours(0, 0, 0, 0);

  const todayCost = sessions
    .filter((s) => s.time.updated * 1000 >= todayStart.getTime())
    .reduce((sum, s) => sum + (s.cost ?? 0), 0);

  const monthCost = sessions
    .filter((s) => s.time.updated * 1000 >= monthStart.getTime())
    .reduce((sum, s) => sum + (s.cost ?? 0), 0);

  // Days elapsed this month (min 1 to avoid division by zero)
  const daysElapsed = Math.max(1, Math.floor((now - monthStart.getTime()) / 86_400_000));
  const projectedMonthly = (monthCost / daysElapsed) * 30;

  return (
    <div className="rounded-xl border border-surface-border bg-surface-raised overflow-hidden" data-testid="cost-tracker">
      <div className="px-3 py-2 border-b border-surface-border">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-bmw-grey/50">Cost</p>
      </div>

      <div className="divide-y divide-surface-border">
        {activeSession && (
          <CostRow
            label="This session"
            value={formatCost(activeCost)}
            highlight
            subtext={activeSession.title ?? activeSession.slug ?? undefined}
          />
        )}
        <CostRow label="Today" value={formatCost(todayCost)} />
        <CostRow
          label="This month"
          value={formatCost(monthCost)}
          subtext={`~${formatCost(projectedMonthly, 2)}/mo projected`}
        />
        <CostRow label="All time" value={formatCost(totalAllTime)} />
      </div>
    </div>
  );
}
