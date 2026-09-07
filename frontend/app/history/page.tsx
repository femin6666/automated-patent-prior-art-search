"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import RiskBadge from "@/components/RiskBadge";
import { SearchHistoryItem } from "@/types";
import { api } from "@/services/api";
import { formatDate } from "@/lib/utils";
import {
  History,
  Search,
  FileText,
  Trash2,
  ExternalLink,
  Loader2,
  Sparkles
} from "lucide-react";

export default function SearchHistoryPage() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [generatingReportId, setGeneratingReportId] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const data = await api.getSearchHistory();
      setHistory(data);
    } catch (err) {
      console.error("Failed to load search history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (searchId: string) => {
    if (!confirm("Are you sure you want to delete this search record?")) return;
    try {
      await api.deleteSearch(searchId);
      setHistory(history.filter((item) => item.id !== searchId));
    } catch (err: any) {
      alert("Failed to delete search: " + err.message);
    }
  };

  const handleGenerateReport = async (searchId: string) => {
    setGeneratingReportId(searchId);
    try {
      const rep = await api.createReport(searchId);
      await api.downloadReportPDF(rep.id, `PatentLens_Report_${searchId.substring(0, 8)}.pdf`);
    } catch (err: any) {
      alert("Failed to generate PDF report: " + err.message);
    } finally {
      setGeneratingReportId(null);
    }
  };

  const filteredHistory = history.filter((item) =>
    item.invention_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.domain.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
            <div>
              <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Search History</h1>
              <p className="text-xs text-zinc-400 mt-0.5">
                Access your past AI prior-art search records and generated reports.
              </p>
            </div>

            <Link
              href="/search"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
            >
              <Search className="w-4 h-4" />
              <span>New Search</span>
            </Link>
          </div>

          {/* Search Filter Bar */}
          <div className="p-3 rounded-xl tech-card flex items-center gap-3">
            <Search className="w-4 h-4 text-indigo-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by invention title or domain..."
              className="w-full bg-transparent text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none"
            />
          </div>

          {/* History List */}
          {loading ? (
            <div className="py-12 text-center">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            </div>
          ) : filteredHistory.length === 0 ? (
            <div className="p-12 text-center rounded-xl tech-card space-y-2 text-xs text-zinc-500">
              <History className="w-6 h-6 text-zinc-600 mx-auto" />
              <p>No prior-art searches found in your history.</p>
            </div>
          ) : (
            <div className="rounded-xl tech-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider bg-zinc-950/60">
                      <th className="p-3.5">Invention Title</th>
                      <th className="p-3.5 whitespace-nowrap">Domain</th>
                      <th className="p-3.5 whitespace-nowrap">Search Date</th>
                      <th className="p-3.5 text-center whitespace-nowrap">Results</th>
                      <th className="p-3.5 text-right whitespace-nowrap">Highest Sim</th>
                      <th className="p-3.5 text-center whitespace-nowrap">Risk Level</th>
                      <th className="p-3.5 text-right whitespace-nowrap">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {filteredHistory.map((item) => (
                      <tr key={item.id} className="hover:bg-zinc-900/60 transition-colors">
                        <td className="p-3.5 font-bold text-zinc-100 max-w-xs truncate" title={item.invention_title}>
                          <Link href={`/search/${item.id}`} className="hover:text-indigo-400 transition-colors">
                            {item.invention_title}
                          </Link>
                        </td>
                        <td className="p-3.5 text-zinc-300 font-medium whitespace-nowrap">{item.domain}</td>
                        <td className="p-3.5 text-zinc-400 font-mono text-[11px] whitespace-nowrap">{formatDate(item.created_at)}</td>
                        <td className="p-3.5 text-center font-mono text-zinc-400 whitespace-nowrap">{item.total_results || 10}</td>
                        <td className="p-3.5 text-right font-mono font-bold text-indigo-400 whitespace-nowrap">
                          {item.highest_similarity}%
                        </td>
                        <td className="p-3.5 text-center whitespace-nowrap">
                          <RiskBadge level={item.risk_level} size="sm" />
                        </td>
                        <td className="p-3.5 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Link
                              href={`/search/${item.id}`}
                              className="p-1.5 rounded-lg bg-zinc-900 text-indigo-400 hover:bg-zinc-800 border border-zinc-800 transition-all"
                              title="View Results"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </Link>
                            
                            <button
                              onClick={() => handleGenerateReport(item.id)}
                              disabled={generatingReportId === item.id}
                              className="p-1.5 rounded-lg bg-zinc-900 text-indigo-400 hover:bg-zinc-800 border border-zinc-800 transition-all"
                              title="Download PDF Report"
                            >
                              {generatingReportId === item.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <FileText className="w-3.5 h-3.5" />
                              )}
                            </button>

                            <button
                              onClick={() => handleDelete(item.id)}
                              className="p-1.5 rounded-lg bg-zinc-900 text-rose-400 hover:bg-zinc-800 border border-zinc-800 transition-all"
                              title="Delete Search"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
