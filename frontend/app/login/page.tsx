"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, X, AlertCircle } from "lucide-react";
import { api } from "@/services/api";

export default function LoginPage() {
  const router = useRouter();
  
  // Tab state: "signup" or "signin"
  const [mode, setMode] = useState<"signup" | "signin">("signin");

  // Form states
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "signin") {
        await api.login({ email, password });
      } else {
        const fullName = `${firstName} ${lastName}`.trim() || email.split("@")[0];
        await api.register({
          name: fullName,
          email,
          password,
          confirm_password: password,
        });
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || (mode === "signin" ? "Invalid login credentials." : "Registration failed."));
    } finally {
      setLoading(false);
    }
  };

  const handleSocialClick = (provider: string) => {
    // For demo purposes: automatic login as demo user
    setError(null);
    setLoading(true);
    setTimeout(() => {
      setEmail("inventor@startup.com");
      setPassword("password123");
      api.login({ email: "inventor@startup.com", password: "password123" })
        .then(() => router.push("/dashboard"))
        .catch((err) => {
          setLoading(false);
          setError("Social auth demo: " + err.message);
        });
    }, 600);
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white relative overflow-hidden">
      
      {/* Warm Ambient Glow Flare (matching the reference image's background gradient) */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-gradient-to-tr from-amber-600/20 via-rose-600/15 to-purple-600/20 rounded-full blur-[140px] pointer-events-none" />

      <main className="flex-1 flex items-center justify-center p-4 py-12 z-10">
        
        {/* Glass Auth Card Container */}
        <div className="w-full max-w-md p-8 rounded-[32px] bg-[#121319]/85 backdrop-blur-2xl border border-white/10 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.8)] relative">
          
          {/* Top Bar: Segmented Switcher & Close Icon */}
          <div className="flex items-center justify-between mb-8">
            
            {/* Sign up / Sign in Switcher Pill */}
            <div className="bg-[#18181f] p-1 rounded-full border border-white/10 inline-flex items-center gap-1">
              <button
                type="button"
                onClick={() => { setMode("signup"); setError(null); }}
                className={`px-5 py-2 rounded-full text-xs transition-all ${
                  mode === "signup"
                    ? "bg-[#282933] text-white font-bold shadow-md"
                    : "text-zinc-400 hover:text-white font-medium"
                }`}
              >
                Sign up
              </button>

              <button
                type="button"
                onClick={() => { setMode("signin"); setError(null); }}
                className={`px-5 py-2 rounded-full text-xs transition-all ${
                  mode === "signin"
                    ? "bg-[#282933] text-white font-bold shadow-md"
                    : "text-zinc-400 hover:text-white font-medium"
                }`}
              >
                Sign in
              </button>
            </div>

            {/* Close Button */}
            <Link
              href="/"
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-all border border-white/10"
              title="Close to Home"
            >
              <X className="w-4 h-4" />
            </Link>
          </div>

          {/* Dynamic Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold tracking-tight text-white">
              {mode === "signup" ? "Create an account" : "Welcome back"}
            </h2>
            <p className="text-xs text-zinc-400 mt-1">
              {mode === "signup"
                ? "Start your AI prior-art research platform"
                : "Sign in to access your saved search reports"}
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Main Auth Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            
            {/* Sign up extra fields: First Name & Last Name */}
            {mode === "signup" && (
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="First name"
                  className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-white/25 focus:bg-white/[0.08] transition-all"
                />
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Last name"
                  className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-white/25 focus:bg-white/[0.08] transition-all"
                />
              </div>
            )}

            {/* Email Field */}
            <div className="relative">
              <Mail className="w-4 h-4 text-zinc-500 absolute left-4 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-white/25 focus:bg-white/[0.08] transition-all"
              />
            </div>

            {/* Password Field */}
            <div className="relative">
              <Lock className="w-4 h-4 text-zinc-500 absolute left-4 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-white/25 focus:bg-white/[0.08] transition-all"
              />
            </div>

            {/* Sign up optional phone input */}
            {mode === "signup" && (
              <div className="flex items-center bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 py-3 text-sm text-white focus-within:border-white/25 focus-within:bg-white/[0.08] transition-all">
                <div className="flex items-center gap-1 pr-3 border-r border-white/10 text-xs font-mono text-zinc-300 select-none">
                  <span>🇺🇸</span>
                  <span className="text-zinc-500 text-[10px]">▼</span>
                </div>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="(775) 351-6501"
                  className="w-full bg-transparent pl-3 focus:outline-none placeholder-zinc-500 text-sm"
                />
              </div>
            )}

            {/* Primary Action Button (Sleek White Metallic Pill) */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-white hover:bg-zinc-200 text-black font-bold text-sm shadow-xl transition-all mt-4 disabled:opacity-50 active:scale-[0.99]"
            >
              {loading
                ? "Processing..."
                : mode === "signup"
                ? "Create an account"
                : "Sign in to account"}
            </button>
          </form>

          {/* OR SIGN IN WITH Separator */}
          <div className="relative my-6 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <span className="relative px-3 bg-[#121319] text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
              OR SIGN IN WITH
            </span>
          </div>

          {/* Social Logins Grid */}
          <div className="grid grid-cols-2 gap-3">
            
            {/* Google Button */}
            <button
              type="button"
              onClick={() => handleSocialClick("google")}
              className="py-3 px-4 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] flex items-center justify-center transition-all group"
              title="Sign in with Google"
            >
              <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
            </button>

            {/* Apple Button */}
            <button
              type="button"
              onClick={() => handleSocialClick("apple")}
              className="py-3 px-4 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] flex items-center justify-center transition-all group"
              title="Sign in with Apple"
            >
              <svg className="w-5 h-5 fill-current text-white group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.32c.68-.83 1.14-1.98.01-3.14-1.02.04-2.25.68-2.98 1.53-.65.75-1.22 1.93-1.06 3.07 1.14.09 2.3-.61 3.03-1.46z" />
              </svg>
            </button>

          </div>

          {/* Footer Disclaimer */}
          <p className="mt-6 text-center text-xs text-zinc-500 font-normal">
            By creating an account, you agree to our{" "}
            <Link href="/" className="underline text-zinc-400 hover:text-white">
              Terms & Service
            </Link>
          </p>

        </div>
      </main>

      <footer className="py-4 text-center text-xs text-zinc-600 font-mono z-10">
        PatentLens AI © 2026
      </footer>
    </div>
  );
}
