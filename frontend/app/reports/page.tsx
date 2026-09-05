"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { Report } from "@/types";
import { api } from "@/services/api";
import { formatDate } from "@/lib/utils";
import { FileText, Download, Loader2, Sparkles, ExternalLink } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadReports() {
      try {
        const data = await api.getReports();
        setReports(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const handleDownload = async (report: Report) => {
    setDownloadingId(report.id);
    try {
      await api.downloadReportPDF(report.id, `PatentLens_Report_${report.search_id.substring(0, 8)}.pdf`);
    } catch (err: any) {
      alert("Failed to download PDF report: " + err.message);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-6xl mx-auto space-y-6">
          
          {/* Header */}
          <div className="pb-4 border-b border-zinc-800/80">
            <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Generated Reports</h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Download your AI-assisted preliminary prior-art PDF search reports.
            </p>
          </div>

          {loading ? (
            <div className="py-12 text-center">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            </div>
          ) : reports.length === 0 ? (
            <div className="p-12 text-center rounded-xl tech-card space-y-2 text-xs text-zinc-500">
              <FileText className="w-6 h-6 text-zinc-600 mx-auto" />
              <p>No PDF search reports generated yet.</p>
              <Link
                href="/history"
                className="inline-block px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium shadow-sm shadow-indigo-500/20"
              >
                Go to History to Generate Reports
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  className="p-5 rounded-xl tech-card space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span className="font-mono text-indigo-400">ID: {rep.search_id.substring(0, 8)}</span>
                      <span className="font-mono text-[11px]">{formatDate(rep.created_at)}</span>
                    </div>

                    <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" />
                      <span>Prior-Art Research Report</span>
                    </h3>
                  </div>

                  <div className="pt-3 border-t border-zinc-800/80 flex items-center justify-between gap-3">
                    <Link
                      href={`/search/${rep.search_id}`}
                      className="text-xs text-zinc-400 hover:text-zinc-100 flex items-center gap-1 transition-colors"
                    >
                      <span>View Search</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>

                    <button
                      onClick={() => handleDownload(rep)}
                      disabled={downloadingId === rep.id}
                      className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-1.5 transition-all shadow-sm shadow-indigo-500/20"
                    >
                      {downloadingId === rep.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                      <span>Download PDF</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
