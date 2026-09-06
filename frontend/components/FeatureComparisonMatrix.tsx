"use client";

import { FeatureComparisonItem } from "@/types";
import { CheckCircle2, AlertCircle, HelpCircle, XCircle } from "lucide-react";

interface FeatureComparisonMatrixProps {
  features?: FeatureComparisonItem[];
}

export default function FeatureComparisonMatrix({ features }: FeatureComparisonMatrixProps) {
  if (!features || features.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-zinc-500 rounded-xl bg-zinc-950/60 border border-zinc-800">
        No direct technical feature comparisons extracted for this document.
      </div>
    );
  }

  const getMatchBadge = (level: string) => {
    switch (level) {
      case "Strong":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Strong
          </span>
        );
      case "Partial":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertCircle className="w-3.5 h-3.5" />
            Partial
          </span>
        );
      case "Weak":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-orange-500/10 text-orange-400 border border-orange-500/30">
            <HelpCircle className="w-3.5 h-3.5" />
            Weak
          </span>
        );
      case "Not Found":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-zinc-800 text-zinc-400 border border-zinc-700">
            <XCircle className="w-3.5 h-3.5" />
            Not Found
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-zinc-100 flex items-center gap-2">
          <span>Technical Feature Comparison</span>
        </h3>
        <span className="text-[11px] font-mono text-zinc-400">
          Comparing target invention vs prior art
        </span>
      </div>

      {/* Responsive Table / Card Grid */}
      <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/70">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-[11px] uppercase tracking-wider bg-zinc-900/60">
              <th className="p-4 w-1/3">Target Feature</th>
              <th className="p-4 w-1/3">Prior-Art Feature</th>
              <th className="p-4 w-28 text-center">Match Level</th>
              <th className="p-4 w-1/3">Technical Explanation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {features.map((item, idx) => (
              <tr key={idx} className="hover:bg-zinc-900/40 transition-colors">
                <td className="p-4 font-semibold text-zinc-200 align-top">
                  <div className="text-indigo-300 font-medium">{item.target_feature}</div>
                </td>
                <td className="p-4 text-zinc-300 align-top">
                  <div className="text-zinc-300">{item.prior_art_feature}</div>
                </td>
                <td className="p-4 text-center align-top">
                  {getMatchBadge(item.match_level)}
                </td>
                <td className="p-4 text-zinc-400 text-[11px] leading-relaxed align-top">
                  {item.explanation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
