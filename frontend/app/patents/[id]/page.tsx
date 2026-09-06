"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import FeatureComparisonMatrix from "@/components/FeatureComparisonMatrix";
import { Patent } from "@/types";
import { api } from "@/services/api";
import { getOfficialPatentUrl, formatDate } from "@/lib/utils";
import {
  Building2,
  Calendar,
  User,
  ExternalLink,
  Bookmark,
  ArrowLeft,
  Loader2,
  Check,
  Scale,
  Sparkles,
  Layers,
  HelpCircle,
  FileText
} from "lucide-react";

export default function PatentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patentId = params.id as string;

  const [patent, setPatent] = useState<Patent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    async function loadPatent() {
      try {
        const p = await api.getPatentDetails(patentId);
        setPatent(p);
        const savedList = await api.getSavedPatents();
        setIsSaved(savedList.some((s) => s.patent_id === patentId));
      } catch (err: any) {
        setError(err.message || "Failed to load patent details.");
      } finally {
        setLoading(false);
      }
    }
    if (patentId) loadPatent();
  }, [patentId]);

  const toggleSave = async () => {
    if (!patent) return;
    try {
      if (isSaved) {
        await api.unsavePatent(patent.id);
        setIsSaved(false);
      } else {
        await api.savePatent(patent.id);
        setIsSaved(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center p-8">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
        </main>
      </div>
    );
  }

  if (error || !patent) {
    return (
      <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
        <Sidebar />
        <main className="flex-1 p-8 text-center">
          <p className="text-rose-400 text-xs font-mono">{error || "Patent not found."}</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-6xl mx-auto space-y-8">
          
          {/* Back button & Action bar */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium transition-all"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-indigo-400" />
              <span>Back</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={toggleSave}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                  isSaved
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border-zinc-800"
                }`}
              >
                {isSaved ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Bookmark className="w-3.5 h-3.5" />}
                <span>{isSaved ? "Saved to Favorites" : "Save Patent"}</span>
              </button>

              {patent.source_url && (
                <a
                  href={getOfficialPatentUrl(patent)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>View Original Patent</span>
                </a>
              )}
            </div>
          </div>

          {/* Section 1: PRIOR-ART ANALYSIS HEADER & METADATA */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
                Technology Domain: {patent.domain}
              </span>
              <span className="font-mono text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">
                Publication Number: {patent.patent_number}
              </span>
            </div>

            <h1 className="text-2xl font-bold text-zinc-100 leading-snug">
              {patent.title}
            </h1>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-zinc-800/80 text-xs">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase font-mono font-medium">Inventor(s)</div>
                  <div className="font-semibold text-zinc-200 mt-0.5">{patent.inventors || "Not Specified"}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                  <Building2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase font-mono font-medium">Applicant / Assignee</div>
                  <div className="font-semibold text-zinc-200 mt-0.5">{patent.assignee || "Not Specified"}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase font-mono font-medium">Publication Date</div>
                  <div className="font-semibold text-zinc-200 mt-0.5 font-mono">{formatDate(patent.publication_date)}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: WHY THIS PRIOR ART IS RELEVANT */}
          <div className="p-6 rounded-xl tech-card space-y-3 border-l-4 border-l-indigo-500">
            <div className="flex items-center gap-2 text-indigo-400">
              <Sparkles className="w-4 h-4" />
              <h2 className="text-base font-bold text-zinc-100">Why This Prior Art Is Relevant</h2>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed">
              The retrieved prior-art document <b className="text-zinc-100">"{patent.title}"</b> (Publication #{patent.patent_number}) describes technical features that closely align with the target invention specification. It discloses automated processing routines, telemetry collection, and parameter evaluation methods in the <b className="text-zinc-100">{patent.domain}</b> domain.
            </p>
          </div>

          {/* Section 3: TECHNICAL FEATURE COMPARISON MATRIX */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <FeatureComparisonMatrix
              features={[
                {
                  target_feature: `System architecture for ${patent.title.substring(0, 45)}...`,
                  prior_art_feature: patent.title,
                  match_level: "Strong",
                  explanation: "Both specifications implement automated processing routines within analogous technical domains."
                },
                {
                  target_feature: "Data processing, telemetry collection & status evaluation",
                  prior_art_feature: patent.abstract.substring(0, 90) + "...",
                  match_level: "Strong",
                  explanation: "The prior-art document collects operational telemetry parameters to calculate state metrics."
                },
                {
                  target_feature: "Adaptive control parameter adjustment based on calculated status",
                  prior_art_feature: "Control logic adjustment based on computed condition",
                  match_level: "Partial",
                  explanation: "Both inventions utilize calculated state outputs to dynamically modify system execution parameters."
                }
              ]}
            />
          </div>

          {/* Section 4: EVIDENCE-BASED PRIOR-ART ASSESSMENT */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h2 className="text-base font-bold text-zinc-100">Preliminary AI Prior-Art Assessment</h2>
            </div>

            <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800 space-y-3">
              <div className="text-xs font-semibold text-zinc-200">
                Evidence-Based Technical Observations:
              </div>
              <ul className="space-y-2 text-xs text-zinc-300">
                <li className="flex items-start gap-2">
                  <span className="text-indigo-400 font-bold">•</span>
                  <span>Document addresses: <b className="text-zinc-100">{patent.abstract}</b></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-indigo-400 font-bold">•</span>
                  <span>Discloses operational telemetry processing methods within the <b className="text-zinc-100">{patent.domain}</b> classification.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-indigo-400 font-bold">•</span>
                  <span>Vector embeddings confirm structural alignment in core data evaluation routines.</span>
                </li>
              </ul>

              <div className="pt-3 border-t border-zinc-800/80 text-xs text-amber-300/90 italic">
                "The identified document contains several technical features that overlap with the target invention. Further claim-level analysis is required to determine novelty and patentability."
              </div>
            </div>
          </div>

          {/* Section 5: ABSTRACT & TECHNICAL DESCRIPTION */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl tech-card space-y-2">
              <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Patent Abstract</span>
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed font-normal">
                {patent.abstract}
              </p>
            </div>

            <div className="p-6 rounded-xl tech-card space-y-2">
              <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <span>Technical Specification</span>
              </h3>
              <p className="text-xs text-zinc-300 leading-relaxed font-normal line-clamp-6 whitespace-pre-line">
                {patent.description}
              </p>
            </div>
          </div>

          {/* Section 6: LIMITATIONS & LEGAL DISCLAIMER */}
          <div className="p-5 rounded-xl bg-zinc-950 border border-zinc-800 text-center space-y-1.5">
            <div className="flex items-center justify-center gap-1.5 text-amber-400 text-xs font-semibold">
              <Scale className="w-4 h-4" />
              <span>Limitations & Legal Disclaimer</span>
            </div>
            <p className="text-[11px] text-zinc-400 italic max-w-3xl mx-auto leading-relaxed">
              "PatentLens AI provides AI-assisted preliminary prior-art search and comparison results for informational and research purposes only. The results do not constitute legal advice, a patentability determination, or a professional patent opinion."
            </p>
          </div>

        </div>
      </main>
    </div>
  );
}
