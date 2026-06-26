// Small inline badge showing a dollar cost value.

interface Props {
  cost: number;
  className?: string;
  prefix?: string;
}

export function CostBadge({ cost, className = "", prefix = "" }: Props) {
  const formatted =
    cost < 0.01
      ? `<$0.01`
      : cost < 1
      ? `$${cost.toFixed(3)}`
      : `$${cost.toFixed(2)}`;

  return (
    <span
      className={`text-xs font-mono text-bmw-grey tabular-nums ${className}`}
      title={`$${cost.toFixed(6)}`}
    >
      {prefix}{formatted}
    </span>
  );
}
