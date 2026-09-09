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
              AI Prior-Art Match
            </div>
            <div className="text-xl font-bold font-mono text-indigo-400">
              {Math.round(final_score)}% <span className="text-xs font-normal text-zinc-400">({simLevel})</span>
            </div>
          </div>
        </div>
      </div>

      {/* Domain & Examination Metric Badges */}
      <div className="space-y-2.5">
        <div className="flex flex-wrap items-center gap-2">
          {(() => {
            const sourceType = patent.source_type || (patent.patent_number.startsWith("ARXIV") ? "arXiv" : "THE LENS");
            const docType = patent.document_type || (patent.patent_number.startsWith("ARXIV") ? "NON-PATENT LITERATURE" : "PATENT");
            const isNPL = docType.includes("NON-PATENT") || sourceType.toLowerCase() === "arxiv";
            return (
              <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold border ${
                isNPL
                  ? "bg-amber-500/10 text-amber-300 border-amber-500/25"
                  : "bg-cyan-500/10 text-cyan-300 border-cyan-500/25"
              }`}>
                Source: {sourceType} • {docType}
              </span>
            );
          })()}
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
            {patent.domain}
          </span>
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            Vector Similarity: {Math.round(semantic_score)}%
          </span>
          {item.technical_feature_coverage !== undefined && item.technical_feature_coverage > 0 && (
            <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20">
              Technical Feature Coverage: {Math.round(item.technical_feature_coverage)}%
            </span>
          )}
          {(() => {
            const hasMatchedFeatures = matched_concepts && matched_concepts.length > 0;
            const isHighRisk = (item.single_document_anticipation === "YES" || final_score > 75) && hasMatchedFeatures;
            const isDetected = hasMatchedFeatures && final_score >= 35;

            if (isHighRisk) {
              return (
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border bg-rose-500/15 text-rose-400 border-rose-500/30">
                  Potential Prior Art: REVIEW REQUIRED
                </span>
              );
            } else if (isDetected) {
              return (
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border bg-amber-500/15 text-amber-400 border-amber-500/30">
                  Prior Art Signal: DETECTED
                </span>
              );
            } else {
              return (
                <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-medium border bg-zinc-900 text-zinc-400 border-zinc-800">
                  Prior Art Signal: NO TECHNICAL OVERLAP
                </span>
              );
            }
          })()}
        </div>

        {(() => {
          const hasMatchedFeatures = matched_concepts && matched_concepts.length > 0;
          const conceptsText = hasMatchedFeatures ? matched_concepts.slice(0, 5).join(", ") : "";
          
          const dynamicExplanation = relevance_explanation && relevance_explanation.length > 15
            ? relevance_explanation
            : hasMatchedFeatures
            ? `Matches ${matched_concepts.length} key technical feature(s): ${conceptsText}.`
            : `Document '${patent.title}' addresses general ${patent.domain} concepts, but zero matching technical features were found in specification text.`;

          return (
            <div className={`p-3 rounded-lg border text-xs leading-relaxed shadow-inner ${
              hasMatchedFeatures ? "bg-zinc-900/70 border-zinc-800 text-zinc-300" : "bg-zinc-950/40 border-zinc-800/60 text-zinc-400"
            }`}>
              <span className="font-semibold text-indigo-400">Why Relevant: </span>
              {dynamicExplanation}
            </div>
          );
        })()}
      </div>

      {/* AI Concept Overlap Chips */}
      <div className="pt-1">
        <ConceptOverlap
          concepts={matched_concepts}
          unmatchedConcepts={item.unmatched_features || item.missing_elements || []}
          technicalFeatures={item.technical_features || []}
        />
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
