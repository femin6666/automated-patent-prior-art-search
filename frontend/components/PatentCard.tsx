"use client";

import { useState } from "react";
import Link from "next/link";
import { SearchResultItem } from "@/types";
import RiskBadge from "./RiskBadge";
import ConceptOverlap from "./ConceptOverlap";
import { Bookmark, ExternalLink, ArrowUpRight, Building2, Calendar, Check } from "lucide-react";
import { api } from "@/services/api";
import { getOfficialPatentUrl, formatDate } from "@/lib/utils";

interface PatentCardProps {
  item: SearchResultItem;
  onSavedToggle?: () => void;
}

export default function PatentCard({ item, onSavedToggle }: PatentCardProps) {
  const { patent, semantic_score, final_score, matched_concepts, rank, semantic_similarity_label, relevance_explanation } = item;
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

  // Derive relevance tag
  const simLevel = semantic_similarity_label || (final_score > 85 ? "Very High" : final_score > 70 ? "High" : final_score > 40 ? "Moderate" : "Low");

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
              <span className="flex items-center gap-1 font-medium text-zinc-400 font-mono text-[11px]">
                <Calendar className="w-3.5 h-3.5 text-zinc-500" />
                {formatDate(patent.publication_date)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto">
          <div className="text-right">
            <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
              AI Semantic Similarity
            </div>
            <div className="text-xl font-bold font-mono text-indigo-400">
              {Math.round(semantic_score || final_score)}% <span className="text-xs font-normal text-zinc-400">({simLevel})</span>
            </div>
          </div>
        </div>
      </div>

      {/* Domain & Relevance Explanation */}
      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
            {patent.domain}
          </span>
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            AI Prior-Art Relevance: {simLevel.toUpperCase()}
          </span>
        </div>

        {relevance_explanation ? (
          <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-300 leading-relaxed">
            <span className="font-semibold text-indigo-400">Why Relevant: </span>
            {relevance_explanation}
          </div>
        ) : (
          <p className="text-xs text-zinc-300 leading-relaxed font-normal line-clamp-3">
            {patent.abstract}
          </p>
        )}
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

          <a
            href={getOfficialPatentUrl(patent)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 transition-all"
          >
            <ExternalLink className="w-3.5 h-3.5 text-zinc-400" />
            <span>View Original Patent</span>
          </a>
        </div>

        <Link
          href={`/patents/${patent.id}`}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
        >
          <span>View Full Feature Comparison</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

    </div>
  );
}
