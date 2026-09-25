"use client";

import React from "react";
import { motion } from "framer-motion";
import { Check } from "lucide-react";

interface LoginButtonProps {
  label: string;
  loading?: boolean;
  success?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: "submit" | "button";
}

export default function LoginButton({
  label,
  loading = false,
  success = false,
  disabled = false,
  onClick,
  type = "submit",
}: LoginButtonProps) {
  return (
    <motion.button
      whileHover={{ y: disabled || loading || success ? 0 : -1 }}
      whileTap={{ y: disabled || loading || success ? 0 : 1, scale: 0.99 }}
      type={type}
      disabled={disabled || loading || success}
      onClick={onClick}
      className={`w-full py-3.5 px-6 rounded-xl font-bold text-sm tracking-wide transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer ${
        success
          ? "bg-emerald-600 text-white shadow-emerald-600/20"
          : "bg-slate-900 hover:bg-slate-800 text-white shadow-slate-900/10"
      } disabled:opacity-60 disabled:cursor-not-allowed`}
    >
      {loading ? (
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          <span>Signing in...</span>
        </div>
      ) : success ? (
        <div className="flex items-center gap-2 animate-in fade-in zoom-in-95">
          <Check className="w-4 h-4" />
          <span>Authenticated</span>
        </div>
      ) : (
        <span>{label}</span>
      )}
    </motion.button>
  );
}
