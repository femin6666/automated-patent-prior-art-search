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
  Loader2
} from "lucide-react";

export default function SearchResultsPage() {
  const params = useParams();
  const router = useRouter();
  const searchId = params.id as string;

  const [data, setData] = useState<PriorArtSearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [sortBy, setSortBy] = useState<"similarity" | "newest" | "oldest">("similarity");
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  useEffect(() => {
    async function fetchSearch() {
      try {
        const res = await api.getSearchDetails(searchId);
        setData(res);
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
      if (riskFilter === "LOW") return score <= 40;
      if (riskFilter === "MODERATE") return score > 40 && score <= 65;
      if (riskFilter === "HIGH") return score > 65 && score <= 80;
      if (riskFilter === "VERY HIGH") return score > 80;
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
                <span className="px-2 py-0.5 text-[10px] font-mono font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Demo Dataset
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

          {/* Prior-Art Relevance Indicator Card */}
          <div className="p-7 rounded-xl tech-card space-y-3 relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-2.5 max-w-2xl">
                <div className="flex items-center gap-2.5">
                  <span className="text-xs font-mono font-semibold text-zinc-400">AI Prior-Art Relevance:</span>
                  <RiskBadge level={data.risk_level} size="md" />
                  <span className="text-xs font-semibold text-zinc-300 font-mono">{data.risk_label}</span>
                </div>
                <h2 className="text-2xl font-bold text-zinc-100">
                  Highest AI Semantic Similarity: <span className="text-indigo-400 font-mono">{Math.round(data.highest_similarity)}%</span>
                </h2>
                <p className="text-xs text-zinc-300 leading-relaxed">
                  The preliminary relevance indicator is computed based on SBERT semantic vector embeddings, technical feature matching, keyword concept overlap, and technology domain alignment.
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
          </div>

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
                <PatentCard key={item.patent.id} item={item} />
              ))
            )}
          </div>

        </div>
      </main>
    </div>
  );
}
