import React from "react";
import { Sparkles, Check, AlertTriangle, X } from "lucide-react";

interface ConceptOverlapProps {
  concepts?: string[];
  unmatchedConcepts?: string[];
  technicalFeatures?: string[];
}

export default function ConceptOverlap({
  concepts = [],
  unmatchedConcepts = [],
  technicalFeatures = []
}: ConceptOverlapProps) {
  const matched = Array.from(new Set(concepts || []));
  const unmatched = Array.from(new Set(unmatchedConcepts || []));
  const allFeatures = Array.from(new Set(technicalFeatures || []));
  
  // Calculate exact total feature count
  const totalCount = Math.max(
    allFeatures.length,
    matched.length + unmatched.length,
    matched.length ? matched.length : 0
  ) || 1;
  const matchedCount = matched.length;

  if (matched.length === 0 && unmatched.length === 0 && allFeatures.length === 0) {
    return (
      <div className="text-xs text-zinc-500 italic">
        No direct concept overlap detected in technical keyword vocabulary.
      </div>
    );
  }

  // Deduplicate unmatched items against matched
  const cleanUnmatched = unmatched.filter(
    u => u && !matched.some(m => m && (m.toLowerCase() === u.toLowerCase() || m.toLowerCase().includes(u.toLowerCase()) || u.toLowerCase().includes(m.toLowerCase())))
  );

  return (
    <div className="space-y-2.5">
      {/* Header and Feature Overlap Counter */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px] font-mono font-semibold text-indigo-400 uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>AI Technical Features</span>
        </div>
        <div className={`px-2.5 py-0.5 rounded-full border text-[11px] font-mono font-bold ${
          matchedCount > 0
            ? "bg-indigo-500/10 border-indigo-500/25 text-indigo-300"
            : "bg-zinc-900 border-zinc-800 text-zinc-400"
        }`}>
          Feature Overlap: {matchedCount} / {totalCount}
        </div>
      </div>

      {/* Chips List with ✓, ✗ status indicators */}
      <div className="flex flex-wrap gap-1.5">
        {/* Matched Concepts (✓) */}
        {matched.map((concept, i) => (
          <span
            key={`m-${i}`}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono font-medium text-emerald-300 bg-emerald-950/40 border border-emerald-500/30"
            title="Matched Technical Feature"
          >
            <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
            <span>{concept}</span>
          </span>
        ))}

        {/* Unmatched or Missing Concepts (✗) */}
        {cleanUnmatched.slice(0, 6).map((concept, i) => (
          <span
            key={`u-${i}`}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono text-zinc-400 bg-zinc-900/60 border border-zinc-800"
            title="Unmatched / Absent in Prior Art"
          >
            <X className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
            <span className="line-through decoration-zinc-600">{concept}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
