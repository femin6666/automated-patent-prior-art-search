"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ConceptOverlap from "@/components/ConceptOverlap";
import { Patent } from "@/types";
import { api } from "@/services/api";
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
  Sparkles
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
        <div className="max-w-6xl mx-auto space-y-6">
          
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
                  href={patent.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Official Source</span>
                </a>
              )}
            </div>
          </div>

          {/* Main Patent Header Card */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
                {patent.domain}
              </span>
              <span className="font-mono text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">
                {patent.patent_number}
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
                  <div className="text-[10px] text-zinc-500 uppercase font-mono font-medium">Inventors</div>
                  <div className="font-semibold text-zinc-200 mt-0.5">{patent.inventors}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                  <Building2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase font-mono font-medium">Assignee</div>
                  <div className="font-semibold text-zinc-200 mt-0.5">{patent.assignee}</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase font-mono font-medium">Publication Date</div>
                  <div className="font-semibold text-zinc-200 mt-0.5 font-mono">{patent.publication_date}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Abstract Section */}
          <div className="p-6 rounded-xl tech-card space-y-2">
            <h2 className="text-base font-bold text-zinc-100">Abstract</h2>
            <p className="text-xs text-zinc-300 leading-relaxed font-normal">
              {patent.abstract}
            </p>
          </div>

          {/* Technical Description */}
          <div className="p-6 rounded-xl tech-card space-y-2">
            <h2 className="text-base font-bold text-zinc-100">Technical Description</h2>
            <p className="text-xs text-zinc-300 leading-relaxed font-normal whitespace-pre-line">
              {patent.description}
            </p>
          </div>

          {/* Side-by-Side Comparison Box */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <h2 className="text-base font-bold text-zinc-100">Technical Concept Comparison Matrix</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800 space-y-2">
                <div className="text-[10px] font-mono font-semibold text-indigo-400 uppercase tracking-wider">
                  Target Patent Document
                </div>
                <div className="text-xs font-bold text-zinc-100">{patent.title}</div>
                <p className="text-xs text-zinc-400 leading-relaxed">{patent.abstract}</p>
                <div className="text-[10px] font-mono text-zinc-500">
                  Assignee: {patent.assignee}
                </div>
              </div>

              <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800 space-y-2">
                <div className="text-[10px] font-mono font-semibold text-indigo-400 uppercase tracking-wider">
                  Prior-Art Assessment Insights
                </div>
                <ul className="space-y-2 text-xs text-zinc-300">
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>Classified under the <b className="text-zinc-100">{patent.domain}</b> technology domain.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>Contains multi-modal sensor/algorithm technical methodologies.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>SBERT embeddings indicate conceptual alignment in system architecture.</span>
                  </li>
                </ul>
              </div>

            </div>
          </div>

          {/* Legal Disclaimer */}
          <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 text-center">
            <p className="text-xs text-zinc-400 italic">
              "PatentLens AI provides AI-assisted preliminary prior-art search results for informational and research purposes only. The results do not constitute legal advice, a patentability determination, or a professional patent opinion."
            </p>
          </div>

        </div>
      </main>
    </div>
  );
}
