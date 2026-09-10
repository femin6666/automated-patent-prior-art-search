"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import DriftWall, { DriftWallItem } from "@/components/DriftWall";
import OptionWheel from "@/components/OptionWheel";
import AnimatedList from "@/components/AnimatedList";
import CountUp from "@/components/CountUp";
import { gsap } from "gsap";
import {
  Sparkles,
  Search,
  Brain,
  Shield,
  FileText,
  ShieldCheck,
  Rocket,
  ArrowRight,
  Plus,
  Lightbulb,
  Cpu,
  Lock,
  Layers,
  CheckCircle2,
  HelpCircle,
  Zap,
  Globe,
  ChevronDown
} from "lucide-react";
import { api } from "@/services/api";

const DRIFT_WALL_ITEMS: DriftWallItem[] = [
  { image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80', title: 'Neural Network' },
  { image: 'https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?auto=format&fit=crop&w=600&q=80', title: 'Quantum Core' },
  { image: 'https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&w=600&q=80', title: 'Robotics' },
  { image: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80', title: 'Circuit Design' },
  { image: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80', title: 'Cyber Security' },
  { image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80', title: 'Global Data' },
  { image: 'https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=600&q=80', title: 'Microchip' },
  { image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=600&q=80', title: 'Data Center' },
  { image: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=600&q=80', title: 'AI Engineering' },
  { image: 'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=600&q=80', title: 'Mathematics' },
  { image: 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=600&q=80', title: 'Biotechnology' },
  { image: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80', title: 'Smart Energy' },
];

const DOMAIN_OPTIONS = [
  "Renewable Energy",
  "Agriculture & AgTech",
  "Biotechnology & Health",
  "Electronics & Software",
  "Medical Devices & MedTech",
  "Artificial Intelligence & ML",
  "CleanTech & Environment",
  "IoT & Embedded Systems",
  "Nanotechnology & Materials",
  "Automotive & Mobility"
];

export default function LandingPage() {
  const router = useRouter();

  const [description, setDescription] = useState(
    "An AI-powered system that analyzes soil conditions and automatically controls irrigation using predictive models."
  );
  const [selectedDomain, setSelectedDomain] = useState("Renewable Energy");
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>(["AI & ML", "Agriculture", "IoT"]);
  const [keywordInput, setKeywordInput] = useState("");
  const [showKeywordInput, setShowKeywordInput] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDomainOpen, setIsDomainOpen] = useState(false);
  const domainDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Close domain dropdown when clicking outside
    const handleClickOutside = (e: MouseEvent) => {
      if (domainDropdownRef.current && !domainDropdownRef.current.contains(e.target as Node)) {
        setIsDomainOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!isDomainOpen) {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isDomainOpen]);

  useEffect(() => {
    // GSAP Hero Entrance Animations with clearProps
    gsap.fromTo(
      ".gsap-hero-content",
      { opacity: 0, x: -30 },
      { opacity: 1, x: 0, duration: 0.9, ease: "power3.out", clearProps: "all" }
    );

    gsap.fromTo(
      ".gsap-3d-visual",
      { opacity: 0, scale: 0.92, y: 20 },
      { opacity: 1, scale: 1, y: 0, duration: 1, delay: 0.2, ease: "power3.out", clearProps: "all" }
    );

    // Continuous GSAP Floating Animations for 3D Cards
    gsap.to(".gsap-float-card-1", {
      y: -12,
      duration: 3,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });

    gsap.to(".gsap-float-card-2", {
      y: 12,
      duration: 3.5,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });

    gsap.to(".gsap-float-card-3", {
      y: -8,
      duration: 2.8,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });

    // Pulsing core animation
    gsap.to(".gsap-pulse-core", {
      scale: 1.08,
      opacity: 0.9,
      duration: 2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut"
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
    <div className="min-h-screen bg-[#07091e] text-zinc-100 font-sans selection:bg-purple-500 selection:text-white relative overflow-hidden">
      
      {/* Radiant Gradient / Creative Mesh Background Layer */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute -top-24 -left-24 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-indigo-600/40 via-purple-600/30 to-pink-500/20 blur-[120px]" />
        <div className="absolute top-1/4 -right-24 w-[700px] h-[700px] rounded-full bg-gradient-to-bl from-cyan-400/30 via-indigo-600/20 to-purple-900/30 blur-[140px]" />
        <div className="absolute -bottom-24 left-1/3 w-[650px] h-[650px] rounded-full bg-gradient-to-tr from-pink-500/25 via-purple-600/20 to-indigo-800/20 blur-[130px]" />
      </div>

      {/* Background React Bits <DriftWall /> Layer */}
      <div className="absolute inset-0 pointer-events-auto z-0 opacity-25 overflow-hidden min-h-[700px]">
        <DriftWall
          items={DRIFT_WALL_ITEMS}
          columns={6}
          tileWidth={220}
          tileHeight={140}
          gap={20}
          tilt={16}
          turn={-14}
          perspective={1200}
          depth={120}
          speed={35}
          direction="up"
          variance={0.45}
          parallax={0.6}
          lift={64}
          fade={0.6}
          dim={0.55}
          overlayColor="#07091e"
        />
      </div>

      {/* Background Neon Aura & Wave Line SVG */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden opacity-30">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="neon-glow" cx="30%" cy="25%" r="50%">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
              <stop offset="50%" stopColor="#a855f7" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#070815" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="right-glow" cx="80%" cy="40%" r="55%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.25" />
              <stop offset="60%" stopColor="#070815" stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#neon-glow)" />
          <rect width="100%" height="100%" fill="url(#right-glow)" />
          
          {/* Wave Mesh Pattern Lines */}
          <path
            d="M -100 600 Q 200 450 500 650 T 1100 600 T 1800 700"
            fill="none"
            stroke="rgba(99, 102, 241, 0.15)"
            strokeWidth="1.5"
          />
          <path
            d="M -100 650 Q 200 500 500 700 T 1100 650 T 1800 750"
            fill="none"
            stroke="rgba(168, 85, 247, 0.12)"
            strokeWidth="1.5"
          />
          <path
            d="M -100 700 Q 200 550 500 750 T 1100 700 T 1800 800"
            fill="none"
            stroke="rgba(56, 189, 248, 0.1)"
            strokeWidth="1"
          />
        </svg>
      </div>

      <Navbar />

      {/* Main Hero Section: Split 2-Column Layout */}
      <section id="search" className="relative pt-28 pb-20 overflow-hidden z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            
            {/* Left Column: Headline, Subtitle, Search Widget & Badges */}
            <div className="lg:col-span-6 space-y-7 gsap-hero-content">
              
              {/* Pill Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#12142d]/80 border border-indigo-500/30 text-xs font-medium text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.2)] backdrop-blur-md">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>Built for MSME Innovators</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.1]">
                From Idea to <br />
                Innovation,{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-400 to-purple-400">
                  Safely.
                </span>
              </h1>

              {/* Subtitle */}
              <p className="text-sm sm:text-base text-zinc-300 leading-relaxed max-w-xl">
                Automatically search and analyze prior art using semantic similarity — so MSME innovators can build with confidence, avoid duplication, and protect their ideas.
              </p>

              {/* Glassmorphic Patent Intelligence Search Box */}
              <div className="relative z-30 p-[1.5px] rounded-2xl bg-indigo-500/30 hover:bg-gradient-to-r hover:from-cyan-400 hover:via-indigo-500 hover:to-purple-500 transition-all duration-300 shadow-[0_0_40px_rgba(99,102,241,0.15)] hover:shadow-[0_0_50px_rgba(99,102,241,0.35),0_0_20px_rgba(56,189,248,0.25)] group/box" ref={domainDropdownRef}>
                
                {/* Solid Dark Inner Content Container (Guarantees interior stays dark) */}
                <div className="relative rounded-[15px] bg-[#0b0e22] p-4 sm:p-5 space-y-4">

                  <form onSubmit={handleAnalyze} className="space-y-3">
                    
                    {/* Search Input Box with Bulb Icon & Gradient Submit Circle */}
                    <div className="relative flex items-center bg-[#060817] border border-white/10 rounded-xl p-2.5 focus-within:border-indigo-500/60 transition-all shadow-inner">
                      <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0 ml-1">
                        <Lightbulb className="w-5 h-5 text-indigo-400" />
                      </div>
                      
                      <input
                        type="text"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Describe your idea or enter keywords... e.g. 'solar water heater', 'biodegradable packaging', 'IoT farming device'"
                        className="w-full bg-transparent px-3 text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none"
                      />

                      {/* Gradient Submit Arrow Button */}
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-blue-500 hover:scale-105 active:scale-95 text-white flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all shrink-0 disabled:opacity-50"
                        title="Analyze Invention"
                      >
                        {isSubmitting ? (
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <ArrowRight className="w-5 h-5 text-white" />
                        )}
                      </button>
                    </div>

                    {/* Keywords & Animated Domain Selection Row */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 px-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {selectedKeywords.map((kw) => (
                          <span
                            key={kw}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/10 text-[11px] font-medium text-zinc-300"
                          >
                            <Sparkles className="w-3 h-3 text-indigo-400" />
                            <span>{kw}</span>
                          </span>
                        ))}

                        {showKeywordInput ? (
                          <input
                            type="text"
                            value={keywordInput}
                            onChange={(e) => setKeywordInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddKeyword())}
                            placeholder="Add keyword..."
                            className="w-24 bg-white/[0.08] border border-white/20 rounded-full px-2.5 py-1 text-[11px] text-white focus:outline-none"
                            autoFocus
                          />
                        ) : (
                          <button
                            type="button"
                            onClick={() => setShowKeywordInput(true)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white/[0.03] border border-white/10 hover:bg-white/[0.08] text-[11px] text-zinc-400 transition-all"
                          >
                            <Plus className="w-3 h-3" />
                            <span>Add Keyword</span>
                          </button>
                        )}
                      </div>

                      {/* Domain Selection Toggle Button */}
                      <div>
                        <button
                          type="button"
                          onClick={() => setIsDomainOpen(!isDomainOpen)}
                          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-[#090c24] border border-indigo-500/40 hover:border-indigo-500/70 text-xs font-semibold text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.2)] hover:scale-105 transition-all cursor-pointer"
                        >
                          <span>{selectedDomain}</span>
                          <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isDomainOpen ? "rotate-180 text-cyan-400" : "text-zinc-400"}`} />
                        </button>
                      </div>

                    </div>

                  </form>
                </div>

                {/* AnimatedList rendered on the right side of the main search box */}
                {isDomainOpen && (
                  <div
                    className="absolute top-full left-1/2 -translate-x-1/2 mt-3 sm:top-1/2 sm:left-full sm:-translate-y-1/2 sm:translate-x-0 sm:mt-0 sm:ml-4 z-[100] w-72 pointer-events-auto flex items-center justify-center animate-in fade-in zoom-in-95 duration-200"
                    onMouseEnter={() => {
                      document.body.style.overflow = "hidden";
                    }}
                    onMouseLeave={() => {
                      document.body.style.overflow = "";
                    }}
                    onWheel={(e) => {
                      e.stopPropagation();
                    }}
                  >
                    <AnimatedList
                      items={DOMAIN_OPTIONS}
                      initialSelectedIndex={Math.max(0, DOMAIN_OPTIONS.indexOf(selectedDomain))}
                      onItemSelect={(item) => {
                        setSelectedDomain(item);
                        setIsDomainOpen(false);
                        document.body.style.overflow = "";
                      }}
                      showGradients={true}
                      enableArrowNavigation={true}
                      displayScrollbar={false}
                    />
                  </div>
                )}
              </div>

              {/* 4 Feature Badges Under Search Box */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 relative z-10">
                
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#0b0e20]/60 border border-white/5 backdrop-blur-md">
                  <span className="text-cyan-400 text-xs">✦</span>
                  <span className="text-[11px] font-semibold text-zinc-300">AI Powered Search</span>
                </div>

                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#0b0e20]/60 border border-white/5 backdrop-blur-md">
                  <span className="text-purple-400 text-xs">⚛</span>
                  <span className="text-[11px] font-semibold text-zinc-300">Semantic Similarity</span>
                </div>

                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#0b0e20]/60 border border-white/5 backdrop-blur-md">
                  <span className="text-indigo-400 text-xs">📑</span>
                  <span className="text-[11px] font-semibold text-zinc-300">Comprehensive Results</span>
                </div>

                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#0b0e20]/60 border border-white/5 backdrop-blur-md">
                  <span className="text-blue-400 text-xs">🛡</span>
                  <span className="text-[11px] font-semibold text-zinc-300">MSME Focused</span>
                </div>

              </div>

            </div>

            {/* Right Column: 3D Holographic AI Brain & Floating Glass Cards (Match User Image) */}
            <div className="lg:col-span-6 relative flex items-center justify-center min-h-[460px] gsap-3d-visual">
              
              {/* Background Glowing Aura Ring */}
              <div className="absolute w-80 h-80 rounded-full bg-gradient-to-tr from-indigo-600/30 via-purple-600/20 to-cyan-500/30 blur-3xl pointer-events-none" />

              {/* Central Isometric 3D Platform Core */}
              <div className="relative w-72 h-72 sm:w-80 sm:h-80 flex items-center justify-center">
                
                {/* 3D Platform Pedestal Base */}
                <div className="absolute bottom-4 w-64 h-32 rounded-[40px] bg-gradient-to-tr from-indigo-900/60 via-purple-900/40 to-blue-900/60 border border-cyan-500/40 shadow-[0_0_50px_rgba(56,189,248,0.3)] transform rotate-x-60 -skew-x-12 backdrop-blur-xl" />
                <div className="absolute bottom-1 w-56 h-24 rounded-[30px] bg-gradient-to-b from-cyan-500/20 to-purple-600/20 border border-indigo-400/30 blur-sm transform rotate-x-60 -skew-x-12" />

                {/* Vertical Hologram Light Beam */}
                <div className="absolute bottom-16 w-32 h-44 bg-gradient-to-t from-cyan-400/20 via-purple-500/10 to-transparent blur-md" />

                {/* Glowing Holographic AI Brain Core Container */}
                <div className="relative w-36 h-36 rounded-3xl bg-[#0a0d26]/80 border border-cyan-400/50 flex items-center justify-center shadow-[0_0_35px_rgba(56,189,248,0.4)] backdrop-blur-2xl gsap-pulse-core">
                  <div className="w-24 h-24 rounded-2xl bg-gradient-to-tr from-indigo-600/40 via-purple-600/40 to-cyan-400/40 p-0.5 flex items-center justify-center">
                    <div className="w-full h-full bg-[#080b21] rounded-[14px] flex items-center justify-center">
                      <Brain className="w-14 h-14 text-cyan-400 drop-shadow-[0_0_15px_rgba(56,189,248,0.8)] animate-pulse" />
                    </div>
                  </div>
                </div>

                {/* Card 1 (Top Left / Front): Patent Document with Similarity 87% Tag */}
                <div className="absolute -top-4 -left-6 sm:-left-10 w-52 p-3.5 rounded-2xl bg-[#0c0f2b]/85 border border-indigo-500/40 shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl gsap-float-card-1">
                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-blue-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold text-white">Patent Document</span>
                  </div>
                  <div className="space-y-1.5">
                    <div className="w-full h-1.5 rounded-full bg-white/10" />
                    <div className="w-3/4 h-1.5 rounded-full bg-white/10" />
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[10px] font-bold text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]">
                      Similarity <CountUp from={0} to={87} duration={2} />%
                    </span>
                  </div>
                </div>

                {/* Card 2 (Top Right): Relevant Patents List with Animated CountUp */}
                <div className="absolute -top-6 -right-6 sm:-right-10 w-56 p-3.5 rounded-2xl bg-[#0c0f2b]/85 border border-purple-500/40 shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl gsap-float-card-2">
                  <div className="flex items-center gap-2 mb-2.5">
                    <Layers className="w-3.5 h-3.5 text-purple-400" />
                    <span className="text-xs font-bold text-white">Relevant Patents</span>
                  </div>
                  
                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex items-center justify-between px-2 py-1 rounded-lg bg-white/[0.04]">
                      <span className="font-bold text-emerald-400">
                        <CountUp from={0} to={87} duration={2} />%
                      </span>
                      <span className="font-mono text-zinc-300">US 10,987,654 B2</span>
                    </div>

                    <div className="flex items-center justify-between px-2 py-1 rounded-lg bg-white/[0.04]">
                      <span className="font-bold text-amber-400">
                        <CountUp from={0} to={76} duration={2} delay={0.2} />%
                      </span>
                      <span className="font-mono text-zinc-300">US 10,456,769 B1</span>
                    </div>

                    <div className="flex items-center justify-between px-2 py-1 rounded-lg bg-white/[0.04]">
                      <span className="font-bold text-cyan-400">
                        <CountUp from={0} to={62} duration={1.8} delay={0.4} />%
                      </span>
                      <span className="font-mono text-zinc-300">US 9,876,543 B2</span>
                    </div>
                  </div>
                </div>

                {/* Card 3 (Bottom Right): Your Idea Protected Badge */}
                <div className="absolute bottom-2 -right-4 sm:-right-8 w-48 p-3 rounded-xl bg-[#0c0f2b]/85 border border-cyan-500/40 shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl gsap-float-card-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400 shrink-0">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white block">Your Idea</span>
                      <span className="text-[10px] text-cyan-300 font-medium">Protected • Original • Safe</span>
                    </div>
                  </div>
                </div>

              </div>

            </div>

          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 border-t border-white/[0.06] relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-2">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              How It Works
            </h2>
            <p className="text-sm font-medium text-zinc-400 tracking-wide">
              Advanced AI. Simple Steps.
            </p>
          </div>

          {/* 4 Connected Step Nodes */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 relative">
            
            {/* Step 01 */}
            <div className="flex flex-col items-center text-center space-y-3 relative group">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-indigo-900/60 to-purple-900/40 border border-indigo-500/40 text-indigo-400 flex items-center justify-center shadow-[0_0_25px_rgba(99,102,241,0.25)] group-hover:scale-110 transition-transform">
                <FileText className="w-7 h-7 text-indigo-300" />
              </div>
              <span className="text-xs font-mono font-bold text-zinc-500">01</span>
              <h3 className="text-base font-bold text-white">Enter Your Idea</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs">
                Type your invention details or keywords in natural language.
              </p>
              
              {/* Connector line for desktop */}
              <div className="hidden lg:block absolute top-8 left-[65%] right-[-35%] h-[1px] bg-gradient-to-r from-indigo-500/50 to-purple-500/20" />
            </div>

            {/* Step 02 */}
            <div className="flex flex-col items-center text-center space-y-3 relative group">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-purple-900/60 to-pink-900/40 border border-purple-500/40 text-purple-400 flex items-center justify-center shadow-[0_0_25px_rgba(168,85,247,0.25)] group-hover:scale-110 transition-transform">
                <Brain className="w-7 h-7 text-purple-300" />
              </div>
              <span className="text-xs font-mono font-bold text-zinc-500">02</span>
              <h3 className="text-base font-bold text-white">Semantic Analysis</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs">
                Our AI understands the meaning and finds relevant concepts.
              </p>

              {/* Connector line for desktop */}
              <div className="hidden lg:block absolute top-8 left-[65%] right-[-35%] h-[1px] bg-gradient-to-r from-purple-500/50 to-cyan-500/20" />
            </div>

            {/* Step 03 */}
            <div className="flex flex-col items-center text-center space-y-3 relative group">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-cyan-900/60 to-blue-900/40 border border-cyan-500/40 text-cyan-400 flex items-center justify-center shadow-[0_0_25px_rgba(56,189,248,0.25)] group-hover:scale-110 transition-transform">
                <Search className="w-7 h-7 text-cyan-300" />
              </div>
              <span className="text-xs font-mono font-bold text-zinc-500">03</span>
              <h3 className="text-base font-bold text-white">Search & Compare</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs">
                Scans millions of patents and identifies similar inventions.
              </p>

              {/* Connector line for desktop */}
              <div className="hidden lg:block absolute top-8 left-[65%] right-[-35%] h-[1px] bg-gradient-to-r from-cyan-500/50 to-emerald-500/20" />
            </div>

            {/* Step 04 */}
            <div className="flex flex-col items-center text-center space-y-3 relative group">
              <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-emerald-900/60 to-teal-900/40 border border-emerald-500/40 text-emerald-400 flex items-center justify-center shadow-[0_0_25px_rgba(16,185,129,0.25)] group-hover:scale-110 transition-transform">
                <ShieldCheck className="w-7 h-7 text-emerald-300" />
              </div>
              <span className="text-xs font-mono font-bold text-zinc-500">04</span>
              <h3 className="text-base font-bold text-white">Get Insights</h3>
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xs">
                View relevant patents, similarity scores and risk analysis.
              </p>
            </div>

          </div>

          {/* Bottom Center Tagline Divider */}
          <div className="mt-16 text-center">
            <span className="text-xs font-mono tracking-[0.3em] uppercase text-zinc-500">
              INNOVATE &nbsp;•&nbsp; SEARCH &nbsp;•&nbsp; PROTECT
            </span>
          </div>

        </div>
      </section>

      {/* Key Features Section */}
      <section id="features" className="py-20 border-t border-white/[0.06] bg-[#060714]/80 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Why Innovators Choose PriorArtIQ
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div className="p-6 rounded-2xl bg-[#090b1c] border border-white/10 hover:border-indigo-500/40 transition-all flex items-start gap-4 shadow-lg">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20 shrink-0">
                <Brain className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white">Understand Meaning</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  We go beyond keywords to understand the deep technical meaning and context of your invention.
                </p>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-[#090b1c] border border-white/10 hover:border-indigo-500/40 transition-all flex items-start gap-4 shadow-lg">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20 shrink-0">
                <Zap className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white">Find Hidden Similarities</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Discover patents that are conceptually identical even if they use completely different terms.
                </p>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-[#090b1c] border border-white/10 hover:border-indigo-500/40 transition-all flex items-start gap-4 shadow-lg">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white">Make Better Decisions</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Get actionable risk indicators and AI insights to protect your intellectual property before filing.
                </p>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="p-8 sm:p-10 rounded-3xl bg-gradient-to-r from-[#0b0e26] via-[#121536] to-[#0a0d24] border border-indigo-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
          
          <div className="flex items-center gap-5">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0 shadow-lg shadow-indigo-500/20">
              <Rocket className="w-7 h-7 text-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Have an idea worth protecting?</h3>
              <p className="text-xs text-zinc-400 mt-1">Start your AI prior-art search in seconds.</p>
            </div>
          </div>

          <Link
            href="/register"
            className="px-7 py-3 rounded-full bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-500 hover:opacity-90 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 self-start sm:self-auto"
          >
            <span>Start Exploring Now</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-white/[0.06] text-center text-xs text-zinc-500 font-mono space-y-2 relative z-10">
        <p>© 2026 PriorArtIQ. Built for MSME Innovators, Researchers & Founders.</p>
      </footer>

    </div>
  );
}