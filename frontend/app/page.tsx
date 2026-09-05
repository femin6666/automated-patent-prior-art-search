"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { gsap } from "gsap";
import {
  Sparkles,
  Search,
  Brain,
  Database,
  Shield,
  FileText,
  Network,
  ShieldCheck,
  Rocket,
  ArrowRight,
  Plus,
  Scale
} from "lucide-react";
import { api } from "@/services/api";

export default function LandingPage() {
  const router = useRouter();

  const [description, setDescription] = useState(
    "An AI-powered system that analyzes soil conditions and automatically controls irrigation using predictive models."
  );
  const [selectedDomain, setSelectedDomain] = useState("Agriculture");
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>(["AI & ML", "Agriculture", "IoT"]);
  const [keywordInput, setKeywordInput] = useState("");
  const [showKeywordInput, setShowKeywordInput] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // GSAP Hero Entrance Animations
    gsap.from(".gsap-hero-title", {
      opacity: 0,
      y: 25,
      duration: 1,
      ease: "power3.out",
    });

    gsap.from(".gsap-hero-widget", {
      opacity: 0,
      y: 35,
      duration: 1.2,
      delay: 0.2,
      ease: "power3.out",
    });

    // Continuous GSAP Floating Animations for Orbit Nodes
    gsap.to(".gsap-orbit-float-1", {
      y: -10,
      duration: 2.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });

    gsap.to(".gsap-orbit-float-2", {
      y: 10,
      duration: 3,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });
  }, []);

  const handleAddKeyword = () => {
    if (keywordInput.trim() && !selectedKeywords.includes(keywordInput.trim())) {
      setSelectedKeywords([...selectedKeywords, keywordInput.trim()]);
      setKeywordInput("");
      setShowKeywordInput(false);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setIsSubmitting(true);
    try {
      const title = description.length > 50 ? description.substring(0, 50) + "..." : description;
      const res = await api.performSearch({
        title: title,
        domain: selectedDomain,
        problem_statement: description,
        description: description,
        keywords: selectedKeywords,
      });
      router.push(`/search/${res.search_id}`);
    } catch (err: any) {
      alert("Failed to run prior-art search: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#05060c] text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white relative overflow-hidden">
      
      {/* Background Constellation Network Graphics */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden opacity-40">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="hero-glow" cx="50%" cy="30%" r="60%">
              <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.25" />
              <stop offset="60%" stopColor="#05060c" stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#hero-glow)" />
          
          {/* Left Side Constellation Nodes */}
          <g stroke="rgba(99, 102, 241, 0.25)" strokeWidth="1" fill="none">
            <line x1="5%" y1="12%" x2="15%" y2="22%" />
            <line x1="15%" y1="22%" x2="10%" y2="45%" />
            <line x1="10%" y1="45%" x2="22%" y2="55%" />
            <line x1="22%" y1="55%" x2="5%" y2="70%" />
            <line x1="15%" y1="22%" x2="25%" y2="30%" />
            <line x1="25%" y1="30%" x2="22%" y2="55%" />

            <circle cx="5%" cy="12%" r="3" fill="#6366f1" />
            <circle cx="15%" cy="22%" r="4" fill="#818cf8" />
            <circle cx="10%" cy="45%" r="3" fill="#38bdf8" />
            <circle cx="22%" cy="55%" r="4" fill="#6366f1" />
            <circle cx="5%" cy="70%" r="3" fill="#818cf8" />
            <circle cx="25%" cy="30%" r="3" fill="#c084fc" />
          </g>

          {/* Right Side Constellation Nodes */}
          <g stroke="rgba(56, 189, 248, 0.25)" strokeWidth="1" fill="none">
            <line x1="95%" y1="15%" x2="82%" y2="28%" />
            <line x1="82%" y1="28%" x2="88%" y2="48%" />
            <line x1="88%" y1="48%" x2="78%" y2="60%" />
            <line x1="78%" y1="60%" x2="92%" y2="75%" />
            <line x1="82%" y1="28%" x2="75%" y2="35%" />

            <circle cx="95%" cy="15%" r="3" fill="#38bdf8" />
            <circle cx="82%" cy="28%" r="4" fill="#38bdf8" />
            <circle cx="88%" cy="48%" r="4" fill="#818cf8" />
            <circle cx="78%" cy="60%" r="3" fill="#c084fc" />
            <circle cx="92%" cy="75%" r="3" fill="#6366f1" />
            <circle cx="75%" cy="35%" r="3" fill="#38bdf8" />
          </g>
        </svg>
      </div>

      <Navbar />

      {/* Main Hero Section */}
      <section className="relative pt-16 pb-24 overflow-hidden z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          
          {/* Hero Headline & Subtitle */}
          <div className="text-center max-w-4xl mx-auto mb-12 relative gsap-hero-title">
            
            {/* Left Orbit Floating Metric 1 (87%) */}
            <div className="hidden lg:flex flex-col items-center absolute -left-28 top-2 gsap-orbit-float-1">
              <div className="w-10 h-10 rounded-full border border-indigo-500/40 bg-[#0c0e1c]/80 flex items-center justify-center text-indigo-400 mb-2 shadow-lg backdrop-blur-md">
                <FileText className="w-5 h-5" />
              </div>
              <div className="w-14 h-14 rounded-full border border-purple-500/50 bg-[#0c0e1c]/90 flex items-center justify-center font-bold text-sm text-purple-300 shadow-[0_0_20px_rgba(168,85,247,0.25)] backdrop-blur-md">
                87%
              </div>
              <span className="text-[11px] text-zinc-300 font-medium mt-1.5">Similarity Score</span>
            </div>

            {/* Left Orbit Floating Metric 2 (62%) */}
            <div className="hidden lg:flex flex-col items-center absolute -left-36 bottom-0 gsap-orbit-float-2">
              <div className="w-10 h-10 rounded-full border border-blue-500/40 bg-[#0c0e1c]/80 flex items-center justify-center text-blue-400 mb-2 shadow-lg backdrop-blur-md">
                <Network className="w-5 h-5" />
              </div>
              <div className="w-14 h-14 rounded-full border border-cyan-500/50 bg-[#0c0e1c]/90 flex items-center justify-center font-bold text-sm text-cyan-300 shadow-[0_0_20px_rgba(6,182,212,0.25)] backdrop-blur-md">
                62%
              </div>
              <span className="text-[11px] text-zinc-300 font-medium mt-1.5">Similarity Score</span>
            </div>

            {/* Right Orbit Floating Metric 1 (91%) */}
            <div className="hidden lg:flex flex-col items-center absolute -right-28 top-8 gsap-orbit-float-2">
              <div className="w-10 h-10 rounded-full border border-indigo-500/40 bg-[#0c0e1c]/80 flex items-center justify-center text-indigo-400 mb-2 shadow-lg backdrop-blur-md">
                <Scale className="w-5 h-5" />
              </div>
              <div className="w-14 h-14 rounded-full border border-indigo-500/50 bg-[#0c0e1c]/90 flex items-center justify-center font-bold text-sm text-indigo-300 shadow-[0_0_20px_rgba(99,102,241,0.25)] backdrop-blur-md">
                91%
              </div>
              <span className="text-[11px] text-zinc-300 font-medium mt-1.5">Similarity Score</span>
            </div>

            {/* Right Orbit Floating Metric 2 (73%) */}
            <div className="hidden lg:flex flex-col items-center absolute -right-36 bottom-4 gsap-orbit-float-1">
              <div className="w-10 h-10 rounded-full border border-blue-500/40 bg-[#0c0e1c]/80 flex items-center justify-center text-blue-400 mb-2 shadow-lg backdrop-blur-md">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="w-14 h-14 rounded-full border border-blue-500/50 bg-[#0c0e1c]/90 flex items-center justify-center font-bold text-sm text-blue-300 shadow-[0_0_20px_rgba(59,130,246,0.25)] backdrop-blur-md">
                73%
              </div>
              <span className="text-[11px] text-zinc-300 font-medium mt-1.5">Similarity Score</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Your Next Idea <br />
              Might Already{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-300">
                Exist.
              </span>
            </h1>

            <p className="mt-5 text-base sm:text-lg text-zinc-300 max-w-2xl mx-auto leading-relaxed">
              Discover hidden technological similarities before investing time, money, and resources into your innovation.
            </p>
          </div>

          {/* Interactive Patent Intelligence Engine Search Box */}
          <div className="max-w-3xl mx-auto rounded-2xl bg-[#090b16]/95 border border-indigo-500/40 p-6 sm:p-7 shadow-[0_0_40px_rgba(99,102,241,0.15)] backdrop-blur-2xl relative gsap-hero-widget">
            
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-mono font-bold text-indigo-400 tracking-wider uppercase">
                PATENT INTELLIGENCE ENGINE
              </span>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-4">
              
              {/* Textarea */}
              <div className="relative">
                <textarea
                  rows={4}
                  maxLength={2000}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your invention in detail..."
                  className="w-full bg-[#05060f]/90 border border-white/10 rounded-xl p-4 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500/60 transition-all leading-relaxed"
                />
                <div className="text-[11px] font-mono text-zinc-500 text-right mt-1">
                  {description.length} / 2000
                </div>
              </div>

              {/* Tags & Action Button Row */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
                
                {/* Keywords Chips */}
                <div className="flex flex-wrap items-center gap-2">
                  {selectedKeywords.map((kw) => (
                    <span
                      key={kw}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/10 text-xs font-medium text-zinc-200"
                    >
                      <Sparkles className="w-3 h-3 text-indigo-400" />
                      <span>{kw}</span>
                    </span>
                  ))}

                  {showKeywordInput ? (
                    <div className="inline-flex items-center gap-1">
                      <input
                        type="text"
                        value={keywordInput}
                        onChange={(e) => setKeywordInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddKeyword())}
                        placeholder="Keyword..."
                        className="w-24 bg-white/[0.08] border border-white/20 rounded-full px-3 py-1 text-xs text-white focus:outline-none"
                        autoFocus
                      />
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setShowKeywordInput(true)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/10 hover:bg-white/[0.08] text-xs font-medium text-zinc-400 transition-all"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add Keyword</span>
                    </button>
                  )}
                </div>

                {/* Primary Action Button */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <span>{isSubmitting ? "Analyzing..." : "Analyze Invention"}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

            </form>
          </div>

        </div>
      </section>

      {/* How PatentLens AI Works Section */}
      <section id="how-it-works" className="py-20 border-t border-white/[0.06] relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              How PatentLens AI Works
            </h2>
          </div>

          {/* 4 Process Cards Row with connected arrows */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start relative">
            
            {/* Step 1 */}
            <div className="text-center space-y-3 p-4 relative">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center justify-center mx-auto shadow-md shadow-indigo-500/10">
                <FileText className="w-7 h-7 text-purple-400" />
              </div>
              <h3 className="text-sm font-bold text-white">1. Understand</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs mx-auto">
                We analyze your invention and extract key concepts.
              </p>
              
              {/* Dotted Arrow 1 */}
              <div className="hidden md:flex items-center absolute top-12 -right-4 w-12 text-indigo-500/40">
                <div className="w-full border-t-2 border-dashed border-indigo-500/40"></div>
                <div className="text-indigo-400 text-xs -ml-1">➔</div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="text-center space-y-3 p-4 relative">
              <div className="w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center mx-auto shadow-md shadow-blue-500/10">
                <Brain className="w-7 h-7 text-blue-400" />
              </div>
              <h3 className="text-sm font-bold text-white">2. Semantic Embedding</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs mx-auto">
                AI converts your description into a rich vector representation.
              </p>

              {/* Dotted Arrow 2 */}
              <div className="hidden md:flex items-center absolute top-12 -right-4 w-12 text-indigo-500/40">
                <div className="w-full border-t-2 border-dashed border-indigo-500/40"></div>
                <div className="text-indigo-400 text-xs -ml-1">➔</div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="text-center space-y-3 p-4 relative">
              <div className="w-16 h-16 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 flex items-center justify-center mx-auto shadow-md shadow-teal-500/10">
                <Database className="w-7 h-7 text-teal-400" />
              </div>
              <h3 className="text-sm font-bold text-white">3. Search & Match</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs mx-auto">
                We search our patent database using semantic similarity.
              </p>

              {/* Dotted Arrow 3 */}
              <div className="hidden md:flex items-center absolute top-12 -right-4 w-12 text-indigo-500/40">
                <div className="w-full border-t-2 border-dashed border-indigo-500/40"></div>
                <div className="text-indigo-400 text-xs -ml-1">➔</div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="text-center space-y-3 p-4">
              <div className="w-16 h-16 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center mx-auto shadow-md shadow-purple-500/10">
                <Shield className="w-7 h-7 text-violet-400" />
              </div>
              <h3 className="text-sm font-bold text-white">4. Prior-Art Insights</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs mx-auto">
                Get ranked results with similarity scores and AI insights.
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* Why Innovators Choose PatentLens AI Feature Cards */}
      <section id="technology" className="py-20 border-t border-white/[0.06] bg-[#070812]/80 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Why Innovators Choose PatentLens AI
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Card 1 */}
            <div className="p-6 rounded-2xl bg-[#090b16] border border-white/10 hover:border-indigo-500/40 transition-all flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20 flex-shrink-0">
                <Brain className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white">Understand Meaning</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  We go beyond keywords to understand the meaning and technical context of your invention.
                </p>
              </div>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-2xl bg-[#090b16] border border-white/10 hover:border-indigo-500/40 transition-all flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20 flex-shrink-0">
                <Network className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white">Find Hidden Similarities</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Discover patents that are conceptually similar but may use different words or descriptions.
                </p>
              </div>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-2xl bg-[#090b16] border border-white/10 hover:border-indigo-500/40 transition-all flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20 flex-shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white">Make Better Decisions</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Get AI-powered insights to evaluate risks, strengthen your idea, and innovate with confidence.
                </p>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* Bottom Call to Action Banner */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="p-8 sm:p-10 rounded-2xl bg-gradient-to-r from-[#090b16] via-[#101224] to-[#0a0c1a] border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-2xl">
          
          <div className="flex items-center gap-5">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/20">
              <Rocket className="w-7 h-7 text-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Have an idea worth protecting?</h3>
              <p className="text-xs text-zinc-400 mt-1">Start your prior-art search in seconds.</p>
            </div>
          </div>

          <Link
            href="/search"
            className="px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 self-start sm:self-auto"
          >
            <span>Start Exploring Now</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

        </div>
      </section>

      {/* Legal Disclaimer & Footer */}
      <footer className="py-10 border-t border-white/[0.06] text-center text-xs text-zinc-500 font-mono space-y-2 relative z-10">
        <p>© 2026 PatentLens AI. Built for Innovators, MSMEs, Students & Researchers.</p>
      </footer>

    </div>
  );
}