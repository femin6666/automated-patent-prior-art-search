import React from "react";
import { CheckCircle2, Sparkles } from "lucide-react";

interface ConceptOverlapProps {
  concepts: string[];
}

export default function ConceptOverlap({ concepts }: ConceptOverlapProps) {
  if (!concepts || concepts.length === 0) {
    return (
      <div className="text-xs text-zinc-500 italic">
        No direct concept overlap detected in technical keyword vocabulary.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-[10px] font-mono font-semibold text-indigo-400 uppercase tracking-wider">
        <Sparkles className="w-3 h-3 text-indigo-400" />
        <span>AI Technical Concept Overlap</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {concepts.map((concept, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono text-zinc-300 bg-zinc-900/90 border border-zinc-800"
          >
            <CheckCircle2 className="w-3 h-3 text-indigo-400" />
            <span>{concept}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
