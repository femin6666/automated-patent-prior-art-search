"use client";

import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Sparkles, ShieldCheck, Brain, TrendingUp, Layers, CheckCircle2 } from "lucide-react";

export type AuthState = "idle" | "emailFocus" | "passwordFocus" | "loading" | "error" | "success";

interface LoginVisualProps {
  authState: AuthState;
}

export default function LoginVisual({ authState }: LoginVisualProps) {
  const shouldReduceMotion = useReducedMotion();

  // Dynamic visual transformation based on interaction state
  const getVisualTransform = () => {
    if (shouldReduceMotion) return { rotateY: 0, rotateX: 0, x: 0, y: 0, scale: 1 };
    switch (authState) {
      case "emailFocus":
        return { rotateY: 6, rotateX: -2, x: 12, y: -4, scale: 1.02 };
      case "passwordFocus":
        return { rotateY: -6, rotateX: 3, x: -8, y: 4, scale: 0.98 };
      case "loading":
        return { rotateY: 0, rotateX: 0, x: 0, y: 0, scale: 0.99 };
      case "error":
        return { rotateY: -8, rotateX: 0, x: -10, y: 0, scale: 0.97 };
      case "success":
        return { rotateY: 0, rotateX: -4, x: 0, y: -16, scale: 1.04 };
      case "idle":
      default:
        return { rotateY: 0, rotateX: 0, x: 0, y: 0, scale: 1 };
    }
  };

  const transform = getVisualTransform();

  return (
    <div className="relative w-full h-full min-h-[480px] lg:min-h-full bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-950 p-8 sm:p-12 lg:p-16 flex flex-col justify-between overflow-hidden selection:bg-indigo-500 selection:text-white">
      
      {/* Background Soft Radiant Gradient Orbs */}
      <div className="absolute top-1/4 left-10 w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-purple-600/15 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-10 right-10 w-64 h-64 bg-cyan-500/15 rounded-full blur-[90px] pointer-events-none" />

      {/* Decorative Top Branding Badge */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs font-semibold text-white">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>PatentLens AI Platform</span>
        </div>
      </div>

      {/* Centerpiece: Layered Product & Analytics Showcase Cards */}
      <div className="relative z-10 my-auto py-8 flex items-center justify-center perspective-1000">
        <motion.div
          animate={{
            rotateY: transform.rotateY,
            rotateX: transform.rotateX,
            x: transform.x,
            y: transform.y,
            scale: transform.scale,
          }}
          transition={{ type: "spring", stiffness: 200, damping: 22 }}
          className="relative w-full max-w-md"
        >
          {/* Main Card: AI Semantic Intelligence Dashboard */}
          <div className="p-6 rounded-3xl bg-slate-900/90 border border-white/15 shadow-[0_20px_50px_rgba(0,0,0,0.5)] backdrop-blur-2xl space-y-4 text-white">
            
            {/* Header row */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold tracking-tight">Semantic Prior-Art Engine</h3>
                  <p className="text-[11px] text-slate-400 font-mono">Neural Search Active</p>
                </div>
              </div>

              <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[10px] font-bold text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                98.4% Match
              </span>
            </div>

            {/* Sparkline & Metrics Preview */}
            <div className="space-y-3 pt-1">
              <div className="flex items-center justify-between text-xs text-slate-300 font-medium">
                <span>Vector Embedding Index</span>
                <span className="text-indigo-400 font-mono">1.2M Patents Analyzed</span>
              </div>

              {/* Simulated Waveform Bar Graph */}
              <div className="flex items-end gap-1.5 h-12 pt-2">
                {[40, 65, 35, 80, 55, 90, 70, 85, 60, 95, 75, 88].map((h, i) => (
                  <motion.div
                    key={i}
                    className="flex-1 rounded-t-sm bg-gradient-to-t from-indigo-600 via-purple-500 to-cyan-400"
                    initial={{ height: "10%" }}
                    animate={{ height: `${h}%` }}
                    transition={{ duration: 0.8, delay: i * 0.05, ease: "easeOut" }}
                  />
                ))}
              </div>
            </div>

            {/* Footer Summary Tag */}
            <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-white/10">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span>Enterprise Grade Security</span>
              </span>
              <span className="font-mono text-xs text-slate-300">v3.4 Production</span>
            </div>

          </div>

          {/* Floating Card 1 (Top Right): Live Patent Count Badge */}
          <motion.div
            className="absolute -top-6 -right-6 p-3.5 rounded-2xl bg-white/10 border border-white/20 backdrop-blur-xl shadow-xl flex items-center gap-3 text-white"
            animate={
              shouldReduceMotion
                ? {}
                : {
                    y: [0, -6, 0],
                  }
            }
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <div className="w-8 h-8 rounded-xl bg-cyan-500/20 border border-cyan-400/30 flex items-center justify-center text-cyan-300">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-300 font-medium">Instant Clearance</div>
              <div className="text-xs font-extrabold text-white font-mono">&lt; 1.2s Real-time</div>
            </div>
          </motion.div>

          {/* Floating Card 2 (Bottom Left): Verified Claims Badge */}
          <motion.div
            className="absolute -bottom-6 -left-6 p-3.5 rounded-2xl bg-slate-900/95 border border-indigo-500/30 backdrop-blur-xl shadow-2xl flex items-center gap-3 text-white"
            animate={
              shouldReduceMotion
                ? {}
                : {
                    y: [0, 6, 0],
                  }
            }
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
          >
            <div className="w-8 h-8 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-400">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 font-medium">Claims Conflict Check</div>
              <div className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Zero Conflicts Found</span>
              </div>
            </div>
          </motion.div>

        </motion.div>
      </div>

      {/* Hero Footer Text */}
      <div className="relative z-10 space-y-1 text-left max-w-md">
        <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight leading-snug">
          Accelerate your R&D from idea to granted patent.
        </h2>
        <p className="text-xs text-slate-400 font-medium leading-relaxed">
          Search millions of global patents in seconds using deep semantic AI analysis.
        </p>
      </div>

    </div>
  );
}
