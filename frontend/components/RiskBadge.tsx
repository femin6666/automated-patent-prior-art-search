import React from "react";

interface RiskBadgeProps {
  level: "LOW" | "MODERATE" | "HIGH" | "VERY HIGH" | string;
  score?: number;
  size?: "sm" | "md" | "lg";
}

export default function RiskBadge({ level, score, size = "md" }: RiskBadgeProps) {
  let badgeStyle = "bg-emerald-500/10 text-emerald-400 border-emerald-500/25";
  let dotColor = "bg-emerald-400";

  switch (level?.toUpperCase()) {
    case "LOW":
      badgeStyle = "bg-emerald-500/10 text-emerald-400 border-emerald-500/25";
      dotColor = "bg-emerald-400";
      break;
    case "MODERATE":
      badgeStyle = "bg-amber-500/10 text-amber-400 border-amber-500/25";
      dotColor = "bg-amber-400";
      break;
    case "HIGH":
      badgeStyle = "bg-orange-500/10 text-orange-400 border-orange-500/25";
      dotColor = "bg-orange-400";
      break;
    case "VERY HIGH":
      badgeStyle = "bg-rose-500/10 text-rose-400 border-rose-500/25";
      dotColor = "bg-rose-400";
      break;
  }

  const sizeClasses = {
    sm: "px-2 py-0.5 text-[10px] font-mono font-medium rounded-full border",
    md: "px-2.5 py-1 text-xs font-mono font-medium rounded-full border",
    lg: "px-3.5 py-1.5 text-xs font-mono font-semibold rounded-full border"
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap ${badgeStyle} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{level} RISK</span>
      {score !== undefined && <span className="opacity-80 font-mono">({score}%)</span>}
    </span>
  );
}
