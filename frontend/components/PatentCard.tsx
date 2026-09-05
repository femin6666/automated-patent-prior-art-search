"use client";

import { useState } from "react";
import Link from "next/link";
import { SearchResultItem } from "@/types";
import RiskBadge from "./RiskBadge";
import ConceptOverlap from "./ConceptOverlap";
import { Bookmark, ExternalLink, ArrowUpRight, Building2, Calendar, Check, Sparkles } from "lucide-react";
import { api } from "@/services/api";

interface PatentCardProps {
  item: SearchResultItem;
  onSavedToggle?: () => void;
}

export default function PatentCard({ item, onSavedToggle }: PatentCardProps) {
  const { patent, final_score, matched_concepts, rank } = item;
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (saved) {
        await api.unsavePatent(patent.id);
        setSaved(false);
      } else {
        await api.savePatent(patent.id);
        setSaved(true);
      }
      if (onSavedToggle) onSavedToggle();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="group relative rounded-xl tech-card tech-card-hover p-6 space-y-4">
      
      {/* Rank & Main Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3.5 border-b border-zinc-800/80">
        <div className="flex items-start gap-3.5">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 font-mono font-bold text-xs flex items-center justify-center border border-indigo-500/25">
            #{rank}
          </div>
          <div>
            <h3 className="text-base font-bold text-zinc-100 group-hover:text-indigo-400 transition-colors leading-snug">
              {patent.title}
            </h3>
            <div className="flex flex-wrap items-center gap-2.5 mt-1 text-xs text-zinc-400">
              <span className="font-mono font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 text-[11px]">
                {patent.patent_number}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-medium text-zinc-300">
                <Building2 className="w-3.5 h-3.5 text-zinc-500" />
                {patent.assignee}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-medium text-zinc-400">
                <Calendar className="w-3.5 h-3.5 text-zinc-500" />
                {patent.publication_date}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 self-end sm:self-auto">
          <div className="text-right">
            <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-500">Hybrid Score</div>
            <div className="text-2xl font-bold font-mono text-indigo-400">
              {final_score}%
            </div>
          </div>
        </div>
      </div>

      {/* Domain & Abstract */}
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
            {patent.domain}
          </span>
        </div>
        <p className="text-xs text-zinc-300 leading-relaxed font-normal line-clamp-3">
          {patent.abstract}
        </p>
      </div>

      {/* AI Concept Overlap Chips */}
      <div className="pt-1">
        <ConceptOverlap concepts={matched_concepts} />
      </div>

      {/* Footer Actions */}
      <div className="pt-3 border-t border-zinc-800/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              saved
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : "bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border-zinc-800"
            }`}
          >
            {saved ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Bookmark className="w-3.5 h-3.5" />}
            <span>{saved ? "Saved" : "Save Patent"}</span>
          </button>

          {patent.source_url && (
            <a
              href={patent.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 transition-all"
            >
              <ExternalLink className="w-3.5 h-3.5 text-zinc-400" />
              <span>Source</span>
            </a>
          )}
        </div>

        <Link
          href={`/patents/${patent.id}`}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
        >
          <span>View Details & Matrix</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

    </div>
  );
}
