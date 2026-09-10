"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import RiskBadge from "@/components/RiskBadge";
import PatentCard from "@/components/PatentCard";
import { SimilarityDistributionChart, Top5SimilarityChart } from "@/components/Charts";
import {
  PriorArtSearchResponse,
  SearchResultItem
} from "@/types";
import { api } from "@/services/api";
import { formatDate } from "@/lib/utils";
import {
  Filter,
  ArrowUpDown,
  Download,
  Scale,
  Sparkles,
  AlertTriangle,
  Loader2,
  HelpCircle,
  X
} from "lucide-react";

export default function SearchResultsPage() {
  const params = useParams();
  const router = useRouter();
  const searchId = params.id as string;

  const [data, setData] = useState<PriorArtSearchResponse | null>(null);
  const [savedPatentIds, setSavedPatentIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [sortBy, setSortBy] = useState<"similarity" | "newest" | "oldest">("similarity");
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [showCalcModal, setShowCalcModal] = useState(false);

  useEffect(() => {
    async function fetchSearch() {
      try {
        const [res, savedList] = await Promise.all([
          api.getSearchDetails(searchId),
          api.getSavedPatents().catch(() => [])
        ]);
        setData(res);
        const ids = new Set<string>();
        savedList.forEach((s) => {
          if (s.patent_id) ids.add(s.patent_id);
          if (s.patent?.id) ids.add(s.patent.id);
          if (s.patent?.patent_number) ids.add(s.patent.patent_number);
        });
        setSavedPatentIds(ids);
      } catch (err: any) {
        setError(err.message || "Failed to load search results.");
      } finally {
        setLoading(false);
      }
    }
    if (searchId) fetchSearch();
  }, [searchId]);

  const handleGenerateReport = async () => {
    if (!data) return;
    setIsGeneratingReport(true);
    try {
      const rep = await api.createReport(data.search_id);
      await api.downloadReportPDF(rep.id, `PatentLens_Report_${data.search_id.substring(0, 8)}.pdf`);
    } catch (err: any) {
      alert("Failed to generate PDF report: " + err.message);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center p-8">
          <div className="text-center space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            <p className="text-xs text-zinc-400 font-mono">Loading prior-art similarity results...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center p-8">
          <div className="p-7 rounded-xl tech-card text-center max-w-md space-y-4">
            <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto" />
            <h2 className="text-lg font-bold text-zinc-100">Error Loading Search</h2>
            <p className="text-xs text-zinc-400">{error || "Search record not found."}</p>
            <button
              onClick={() => router.push("/search")}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium"
            >
              Back to New Search
            </button>
          </div>
        </main>
      </div>
    );
  }

  let filteredResults = [...data.results];

  if (riskFilter !== "ALL") {
    filteredResults = filteredResults.filter((r) => {
      const score = r.final_score;
      if (riskFilter === "LOW") return score < 40;
      if (riskFilter === "MODERATE") return score >= 40 && score < 70;
      if (riskFilter === "HIGH") return score >= 70 && score < 85;
      if (riskFilter === "VERY HIGH") return score >= 85;
      return true;
    });
  }

  if (sortBy === "similarity") {
    filteredResults.sort((a, b) => b.final_score - a.final_score);
  } else if (sortBy === "newest") {
    filteredResults.sort((a, b) => new Date(b.patent.publication_date).getTime() - new Date(a.patent.publication_date).getTime());
  } else if (sortBy === "oldest") {
    filteredResults.sort((a, b) => new Date(a.patent.publication_date).getTime() - new Date(b.patent.publication_date).getTime());
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-7xl mx-auto space-y-8">
          
          {/* Header & Controls */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
                  {data.domain}
                </span>
                <span className="text-xs text-zinc-400 font-mono">• {formatDate(data.created_at)}</span>
                <span className="px-2 py-0.5 text-[10px] font-mono font-medium rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {data.data_source || "Live arXiv Feed"}
                </span>
              </div>
              <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Prior-Art Analysis Results</h1>
              <p className="text-xs text-zinc-300 font-medium mt-0.5">
                Invention: "{data.invention_title}"
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleGenerateReport}
                disabled={isGeneratingReport}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
              >
                {isGeneratingReport ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                <span>{isGeneratingReport ? "Generating PDF..." : "Download PDF Report"}</span>
              </button>
            </div>
          </div>

          {/* Search Summary Counts */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-4 rounded-xl tech-card text-center">
              <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider">Total Matches</div>
              <div className="text-2xl font-mono font-bold text-zinc-100 mt-1">{data.summary.total_results}</div>
            </div>
            <div className="p-4 rounded-xl tech-card text-center">
              <div className="text-[10px] text-emerald-400 font-mono uppercase tracking-wider">Low Risk</div>
              <div className="text-2xl font-mono font-bold text-emerald-400 mt-1">{data.summary.low_similarity}</div>
            </div>
            <div className="p-4 rounded-xl tech-card text-center">
              <div className="text-[10px] text-amber-400 font-mono uppercase tracking-wider">Moderate Risk</div>
              <div className="text-2xl font-mono font-bold text-amber-400 mt-1">{data.summary.moderate_similarity}</div>
            </div>
            <div className="p-4 rounded-xl tech-card text-center">
              <div className="text-[10px] text-orange-400 font-mono uppercase tracking-wider">High Risk</div>
              <div className="text-2xl font-mono font-bold text-orange-400 mt-1">{data.summary.high_similarity}</div>
            </div>
            <div className="p-4 rounded-xl tech-card text-center col-span-2 sm:col-span-1">
              <div className="text-[10px] text-rose-400 font-mono uppercase tracking-wider">Very High Risk</div>
              <div className="text-2xl font-mono font-bold text-rose-400 mt-1">{data.summary.very_high_similarity}</div>
            </div>
          </div>

          {/* Patent API Execution Audit Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20">
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-indigo-300">Searched</div>
              <div className="text-xl font-mono font-bold text-indigo-200 mt-0.5">
                {data.summary.pipeline_metrics?.patents_searched || data.summary.patents_searched || 100}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-sky-300">API Retrieved</div>
              <div className="text-xl font-mono font-bold text-sky-200 mt-0.5">
                {data.summary.pipeline_metrics?.patents_retrieved || data.summary.patents_retrieved || 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-purple-300">Shortlisted</div>
              <div className="text-xl font-mono font-bold text-purple-200 mt-0.5">
                {data.summary.pipeline_metrics?.vector_shortlisted || data.summary.patents_shortlisted || data.results.length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-300">Unique Families</div>
              <div className="text-xl font-mono font-bold text-emerald-200 mt-0.5">
                {data.summary.pipeline_metrics?.unique_families || data.summary.unique_families_count || data.results.length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-300">With Claims</div>
              <div className="text-xl font-mono font-bold text-cyan-200 mt-0.5">
                {data.summary.pipeline_metrics?.patents_with_claims || 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-amber-300">Full Text</div>
              <div className="text-xl font-mono font-bold text-amber-200 mt-0.5">
                {data.summary.pipeline_metrics?.patents_with_full_text || 0}
              </div>
            </div>
            <div className="text-center">
              <div className="text-[10px] font-mono uppercase tracking-wider text-rose-300">Evidence Verified</div>
              <div className="text-xl font-mono font-bold text-rose-200 mt-0.5">
                {data.summary.pipeline_metrics?.evidence_verified_matches || 0}
              </div>
            </div>
          </div>

          {/* Prior-Art Relevance Indicator Card */}
          {(() => {
            const topMatchScore = data.results && data.results.length > 0 ? Math.round(data.results[0].final_score) : Math.round(data.highest_similarity);
            const topVectorSim = data.results && data.results.length > 0 ? Math.round(data.results[0].semantic_score) : Math.round(data.highest_semantic_similarity || data.highest_similarity);
            const topScoreBreakdown = data.results[0]?.score_breakdown || {
              semantic_similarity: topVectorSim,
              technical_features: data.results[0]?.keyword_score || 0,
              evidence_strength: data.results[0]?.evidence_confidence || 0,
              distinctive_concepts: data.results[0]?.keyword_score || 0,
              domain_cpc_alignment: data.results[0]?.domain_score || 50,
              final_score: topMatchScore,
              is_gated: false,
              formula_explanation: "Final Score = (25% Semantic) + (40% Technical Features) + (15% Evidence) + (10% Distinctive Concepts) + (10% Domain/CPC)"
            };

            return (
              <div className="p-7 rounded-xl tech-card space-y-3 relative overflow-hidden">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-2.5 max-w-2xl">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-mono font-semibold text-zinc-400">AI Preliminary Prior-Art Relevance:</span>
                      <RiskBadge level={data.risk_level} size="md" />
                      <span className="text-xs font-semibold text-zinc-300 font-mono">{data.risk_label}</span>
                    </div>
                    <h2 className="text-2xl font-bold text-zinc-100 flex flex-wrap items-center gap-3">
                      <span>Overall Technical Relevance:</span>
                      <span className="text-indigo-400 font-mono">{Math.round(data.highest_similarity)}%</span>
                      <span className="px-3 py-1 rounded-md bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 text-xs font-mono font-semibold shadow-sm">
                        Highest SBERT Semantic: {topVectorSim}%
                      </span>
                      <button
                        onClick={() => setShowCalcModal(true)}
                        className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-mono text-indigo-400 hover:text-indigo-300 transition-all cursor-pointer shadow-sm"
                      >
                        <HelpCircle className="w-3.5 h-3.5" />
                        <span>How is this calculated?</span>
                      </button>
                    </h2>
                    <p className="text-xs text-zinc-300 leading-relaxed">
                      The preliminary relevance score is computed by the deterministic backend scoring engine using 25% SBERT Semantic Vector Similarity, 40% Technical Feature Score, 15% Evidence Verification, 10% Distinctive Concept Overlap, and 10% Domain/CPC Alignment.
                    </p>
                  </div>

                  <div className="p-4 rounded-lg bg-zinc-900/80 border border-zinc-800 max-w-xs text-xs space-y-1.5">
                    <div className="flex items-center gap-1.5 text-amber-400 font-mono text-[11px] font-semibold">
                      <Scale className="w-3.5 h-3.5" />
                      <span>Preliminary AI Disclaimer</span>
                    </div>
                    <p className="text-[11px] text-zinc-400 leading-relaxed italic">
                      {data.disclaimer}
                    </p>
                  </div>
                </div>

                {/* Calculation Breakdown Modal */}
                {showCalcModal && (
                  <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="w-full max-w-lg p-6 rounded-2xl bg-[#0c0e24] border border-indigo-500/30 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9)] space-y-4 text-left">
                      <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                        <div className="flex items-center gap-2 text-indigo-400 font-mono font-bold text-sm">
                          <HelpCircle className="w-4 h-4" />
                          <span>Authoritative Score Calculation Formula</span>
                        </div>
                        <button
                          onClick={() => setShowCalcModal(false)}
                          className="w-7 h-7 rounded-full bg-white/5 hover:bg-white/15 text-white flex items-center justify-center transition-all border border-white/10"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="space-y-3 text-xs">
                        <p className="text-zinc-300 leading-relaxed">
                          The <strong>Overall Prior-Art Technical Relevance Score ({Math.round(data.highest_similarity)}%)</strong> evaluates prior art candidates using the authoritative single-source formula:
                        </p>

                        <div className="p-4 rounded-xl bg-[#070919] border border-indigo-500/20 font-mono text-[11px] space-y-2.5">
                          <div className="flex justify-between items-center text-sky-300">
                            <span>1. Technical Feature Score (40% Weight):</span>
                            <span className="font-bold text-white">{topScoreBreakdown.technical_features}%</span>
                          </div>
                          <div className="flex justify-between items-center text-indigo-300">
                            <span>2. SBERT Semantic Similarity (25% Weight):</span>
                            <span className="font-bold text-white">{topScoreBreakdown.semantic_similarity}%</span>
                          </div>
                          <div className="flex justify-between items-center text-emerald-300">
                            <span>3. Evidence Text Strength (15% Weight):</span>
                            <span className="font-bold text-white">{topScoreBreakdown.evidence_strength}%</span>
                          </div>
                          <div className="flex justify-between items-center text-amber-300">
                            <span>4. Distinctive Concept Match (10% Weight):</span>
                            <span className="font-bold text-white">{topScoreBreakdown.distinctive_concepts}%</span>
                          </div>
                          <div className="flex justify-between items-center text-purple-300">
                            <span>5. Domain & CPC/IPC Alignment (10% Weight):</span>
                            <span className="font-bold text-white">{topScoreBreakdown.domain_cpc_alignment}%</span>
                          </div>
                          <div className="pt-2 border-t border-zinc-800 flex justify-between items-center text-white text-xs font-bold">
                            <span>Overall Relevance Score:</span>
                            <span className="text-indigo-400 font-mono text-sm">{topScoreBreakdown.final_score}%</span>
                          </div>
                        </div>

                        {topScoreBreakdown.is_gated && (
                          <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-[11px]">
                            ⚠️ <strong>Technical Relevance Gate Applied:</strong> The final score was capped because the technical feature overlap score is under 20%.
                          </div>
                        )}

                        <p className="text-[11px] text-zinc-400 italic leading-relaxed">
                          {topScoreBreakdown.formula_explanation}
                        </p>
                      </div>

                      <button
                        onClick={() => setShowCalcModal(false)}
                        className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 transition-all cursor-pointer"
                      >
                        Close Calculation Breakdown
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Recharts Visualizations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl tech-card space-y-3">
              <h3 className="text-base font-bold text-zinc-100">Similarity Distribution</h3>
              <SimilarityDistributionChart summary={data.summary} />
            </div>

            <div className="p-6 rounded-xl tech-card space-y-3">
              <h3 className="text-base font-bold text-zinc-100">Top 5 Similar Patents</h3>
              <Top5SimilarityChart results={data.results} />
            </div>
          </div>

          {/* Filter & Sort Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl tech-card">
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5 font-medium text-zinc-300">
                <Filter className="w-3.5 h-3.5 text-indigo-400" />
                <span>Risk Filter:</span>
              </div>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="px-3 py-1.5 rounded-lg tech-input text-xs font-medium focus:outline-none"
              >
                <option value="ALL" className="bg-[#09090b]">All Risk Levels ({data.results.length})</option>
                <option value="LOW" className="bg-[#09090b]">Low Risk</option>
                <option value="MODERATE" className="bg-[#09090b]">Moderate Risk</option>
                <option value="HIGH" className="bg-[#09090b]">High Risk</option>
                <option value="VERY HIGH" className="bg-[#09090b]">Very High Risk</option>
              </select>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5 font-medium text-zinc-300">
                <ArrowUpDown className="w-3.5 h-3.5 text-indigo-400" />
                <span>Sort By:</span>
              </div>
              <select
                value={sortBy}
                onChange={(e: any) => setSortBy(e.target.value)}
                className="px-3 py-1.5 rounded-lg tech-input text-xs font-medium focus:outline-none"
              >
                <option value="similarity" className="bg-[#09090b]">Highest Similarity</option>
                <option value="newest" className="bg-[#09090b]">Newest Publication</option>
                <option value="oldest" className="bg-[#09090b]">Oldest Publication</option>
              </select>
            </div>
          </div>

          {/* Patent Results Cards */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-zinc-100">
              Top Relevant Prior-Art Patent Documents ({filteredResults.length})
            </h2>

            {filteredResults.length === 0 ? (
              <div className="p-8 text-center text-zinc-500 rounded-xl tech-card text-xs">
                No patents match the selected filter criteria.
              </div>
            ) : (
              filteredResults.map((item) => (
                <PatentCard
                  key={item.patent.id}
                  item={item}
                  isInitialSaved={savedPatentIds.has(item.patent.id) || savedPatentIds.has(item.patent.patent_number)}
                />
              ))
            )}
          {/* Legal Disclaimer Footer */}
          <div className="mt-8 p-4 rounded-xl bg-zinc-950/80 border border-zinc-800/80 text-[11px] text-zinc-400 leading-relaxed font-mono flex items-start gap-3">
            <Scale className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-zinc-200 uppercase tracking-wider block mb-0.5">Legal Disclaimer</span>
              PatentLens AI provides AI-assisted preliminary technical prior-art relevance analysis. Results are intended for research and screening purposes and do not constitute a legal opinion or definitive patentability determination. Professional patent review is recommended before filing or making legal decisions.
            </div>
          </div>
        </div>
      </div>
      </main>
    </div>

  );
}
