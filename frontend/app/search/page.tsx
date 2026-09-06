"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import {
  Sparkles,
  Tag,
  X,
  Plus,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Scale,
  Cpu
} from "lucide-react";
import { api } from "@/services/api";

const DOMAIN_OPTIONS = [
  "Artificial Intelligence",
  "Agriculture",
  "Healthcare",
  "IoT",
  "Robotics",
  "Energy",
  "Manufacturing",
  "Software",
  "Electronics",
  "Biotechnology",
  "Other"
];

const PROCESSING_STAGES = [
  "Understanding invention context",
  "Extracting technical concepts",
  "Generating SBERT 384-d semantic embedding",
  "Searching patent vector database",
  "Calculating hybrid similarity & domain scores",
  "Ranking top relevant patent prior art"
];

export default function NewSearchPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [domain, setDomain] = useState("Artificial Intelligence");
  const [problemStatement, setProblemStatement] = useState("");
  const [description, setDescription] = useState("");
  
  const [keywords, setKeywords] = useState<string[]>(["Machine Learning", "IoT"]);
  const [keywordInput, setKeywordInput] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStage, setActiveStage] = useState(0);

  const addKeyword = () => {
    const trimmed = keywordInput.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      setKeywords([...keywords, trimmed]);
      setKeywordInput("");
    }
  };

  const removeKeyword = (tagToRemove: string) => {
    setKeywords(keywords.filter((t) => t !== tagToRemove));
  };

  const handleKeyDownKeyword = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addKeyword();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError("Invention title is required.");
      return;
    }
    if (problemStatement.trim().length < 10) {
      setError("Problem statement must be at least 10 characters long.");
      return;
    }
    if (description.trim().length < 20) {
      setError("Detailed invention description must be at least 20 characters long.");
      return;
    }

    setIsProcessing(true);
    setActiveStage(0);

    const interval = setInterval(() => {
      setActiveStage((prev) => {
        if (prev < PROCESSING_STAGES.length - 1) return prev + 1;
        return prev;
      });
    }, 600);

    try {
      const response = await api.performSearch({
        title,
        domain,
        problem_statement: problemStatement,
        description,
        keywords,
      });

      clearInterval(interval);
      router.push(`/search/${response.search_id}`);
    } catch (err: any) {
      clearInterval(interval);
      setIsProcessing(false);
      setError(err.message || "Failed to execute prior-art search.");
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-4xl mx-auto space-y-8">
          
          {/* Page Header */}
          <div className="pb-4 border-b border-zinc-800/80">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-mono font-medium mb-2">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>AI Vector Matcher</span>
            </div>
            <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">New Prior-Art Search</h1>
            <p className="text-xs text-zinc-400 mt-1">
              Submit your invention details to compute SBERT vector embeddings and perform hybrid similarity search.
            </p>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Invention Title */}
            <div className="p-6 rounded-xl tech-card space-y-2">
              <label className="block text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">Invention Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. AI-Based Smart Irrigation System"
                className="w-full px-4 py-2.5 rounded-lg tech-input text-sm text-zinc-100 placeholder-zinc-500"
              />
            </div>

            {/* Technology Domain Dropdown */}
            <div className="p-6 rounded-xl tech-card space-y-2">
              <label className="block text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">Technology Domain *</label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg tech-input text-sm text-zinc-100 focus:outline-none"
              >
                {DOMAIN_OPTIONS.map((d) => (
                  <option key={d} value={d} className="bg-[#09090b] text-zinc-100">
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* Problem Statement */}
            <div className="p-6 rounded-xl tech-card space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">Problem Statement *</label>
                <span className="text-[11px] text-zinc-500">What problem does your invention solve?</span>
              </div>
              <textarea
                required
                rows={3}
                value={problemStatement}
                onChange={(e) => setProblemStatement(e.target.value)}
                placeholder="e.g. Existing agricultural watering systems cause excessive water consumption due to fixed timer schedules that ignore local soil moisture and rainfall..."
                className="w-full px-4 py-2.5 rounded-lg tech-input text-sm text-zinc-100 placeholder-zinc-500"
              />
            </div>

            {/* Detailed Description */}
            <div className="p-6 rounded-xl tech-card space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">Detailed Invention Description *</label>
                <span className="text-[11px] text-zinc-500 font-mono">Min 20 chars</span>
              </div>
              <textarea
                required
                rows={6}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe how your invention works, the technologies involved, important components, workflow, technical methods, and what makes your invention different..."
                className="w-full px-4 py-2.5 rounded-lg tech-input text-sm text-zinc-100 placeholder-zinc-500"
              />
            </div>

            {/* Keywords Tag Selector */}
            <div className="p-6 rounded-xl tech-card space-y-3">
              <label className="block text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">Keywords & Key Concepts</label>
              
              <div className="flex items-center gap-2.5">
                <div className="relative flex-1">
                  <Tag className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    value={keywordInput}
                    onChange={(e) => setKeywordInput(e.target.value)}
                    onKeyDown={handleKeyDownKeyword}
                    placeholder="Type a keyword tag and press Enter (e.g. Machine Learning)"
                    className="w-full pl-10 pr-4 py-2 rounded-lg tech-input text-xs text-zinc-100 placeholder-zinc-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={addKeyword}
                  className="px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-200 font-medium text-xs border border-zinc-800 flex items-center gap-1.5 transition-all"
                >
                  <Plus className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Add Tag</span>
                </button>
              </div>

              {/* Tag Chips */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {keywords.map((kw) => (
                  <span
                    key={kw}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900 text-zinc-300 border border-zinc-800 text-xs font-mono"
                  >
                    <span>{kw}</span>
                    <button
                      type="button"
                      onClick={() => removeKeyword(kw)}
                      className="hover:text-rose-400 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isProcessing}
                className="w-full py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-sm shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4 text-indigo-200" />
                <span>Analyze Prior Art</span>
              </button>
            </div>

          </form>

          {/* Legal Disclaimer */}
          <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 flex items-start gap-3">
            <Scale className="w-4 h-4 text-zinc-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-zinc-400 leading-relaxed italic">
              "PatentLens AI provides AI-assisted preliminary prior-art search results for informational and research purposes only. The results do not constitute legal advice, a patentability determination, or a professional patent opinion."
            </p>
          </div>

        </div>
      </main>

      {/* AI Processing Screen Modal */}
      {isProcessing && (
        <div className="fixed inset-0 z-50 bg-[#09090b]/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-md p-7 rounded-xl tech-card shadow-2xl text-center space-y-5 relative">
            
            <div className="w-14 h-14 mx-auto rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/30 glow-indigo">
              <Cpu className="w-7 h-7 text-indigo-400" />
            </div>

            <div>
              <h2 className="text-xl font-bold text-zinc-100">Analyzing Invention Prior Art</h2>
              <p className="text-xs text-zinc-400 mt-1">Computing SBERT embeddings & vector similarity search...</p>
            </div>

            {/* Stages Checklist */}
            <div className="space-y-3 text-left bg-zinc-950 p-4 rounded-lg border border-zinc-800">
              {PROCESSING_STAGES.map((stage, idx) => {
                const isDone = idx < activeStage;
                const isCurrent = idx === activeStage;
                return (
                  <div key={idx} className="flex items-center gap-2.5 text-xs">
                    {isDone ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    ) : isCurrent ? (
                      <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin flex-shrink-0" />
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full border border-zinc-800 flex-shrink-0" />
                    )}
                    <span className={isDone ? "text-zinc-500 line-through opacity-60 font-mono text-[11px]" : isCurrent ? "text-indigo-400 font-bold font-mono text-[11px]" : "text-zinc-600 font-mono text-[11px]"}>
                      {stage}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
