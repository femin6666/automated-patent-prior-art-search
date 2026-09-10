"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, Lock, X, AlertCircle, CheckCircle, ArrowRight, KeyRound, Sparkles } from "lucide-react";
import { api } from "@/services/api";
import {
  auth,
  googleProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  updateProfile
} from "@/lib/firebase";
import { sendAuthEmail, sendOTPEmail } from "@/lib/emailjs";

export default function LoginPage() {
  const router = useRouter();

  // Tab mode: "signin", "signup", or "forgot"
  const [mode, setMode] = useState<"signin" | "signup" | "forgot">("signin");

  // Form states
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // OTP First-Time Verification states
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [otpCodeInput, setOtpCodeInput] = useState("");
  const [demoOTP, setDemoOTP] = useState<string | null>(null);
  const [otpTargetEmail, setOtpTargetEmail] = useState("");

  // Status states
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Handle Form Submit (Sign In, Sign Up, or Password Reset)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (mode === "forgot") {
        await sendPasswordResetEmail(auth, email);
        await sendAuthEmail({
          toEmail: email,
          toName: email.split("@")[0],
          actionType: "reset_password"
        });
        setSuccessMsg("Password reset email sent! Check your inbox for instructions.");
        setLoading(false);
        return;
      }

      if (mode === "signin") {
        let authRes: any;
        try {
          try {
            const cred = await signInWithEmailAndPassword(auth, email, password);
            const user = cred.user;
            authRes = await api.login({ email: user.email || email, password });
          } catch (fbErr: any) {
            console.warn("[Firebase Auth] Falling back to backend auth API:", fbErr.message);
            authRes = await api.login({ email, password });
          }
        } catch (loginErr: any) {
          const errMsg = loginErr.message || "";
          if (errMsg.toLowerCase().includes("no account found") || errMsg.toLowerCase().includes("not found")) {
            setMode("signup");
            setError("No account found with this email address. We've switched you to Sign Up to create your account!");
            setLoading(false);
            return;
          }
          throw loginErr;
        }

        if (authRes?.require_otp) {
          const activeOtpCode = (authRes.demo_otp && String(authRes.demo_otp).length === 6)
            ? String(authRes.demo_otp)
            : Math.floor(100000 + Math.random() * 900000).toString();
          setOtpTargetEmail(authRes.otp_sent_to || email);
          setDemoOTP(activeOtpCode);
          setShowOTPModal(true);
          sendOTPEmail({ toEmail: authRes.otp_sent_to || email, otpCode: activeOtpCode })
            .then((res) => console.log("[Login EmailJS OTP]", res))
            .catch((err) => console.warn("[Login EmailJS OTP Error]", err));
          setLoading(false);
          return;
        }

        router.push("/dashboard");
      } else {
        // Sign Up Mode
        const fullName = `${firstName} ${lastName}`.trim() || email.split("@")[0];
        let authRes: any;

        try {
          const cred = await createUserWithEmailAndPassword(auth, email, password);
          if (cred.user) {
            await updateProfile(cred.user, { displayName: fullName });
          }
          authRes = await api.register({
            name: fullName,
            email,
            password,
            confirm_password: password
          });
        } catch (fbErr: any) {
          console.warn("[Firebase Auth] Falling back to backend register API:", fbErr.message);
          authRes = await api.register({
            name: fullName,
            email,
            password,
            confirm_password: password
          });
        }

        if (authRes?.require_otp) {
          const activeOtpCode = (authRes.demo_otp && String(authRes.demo_otp).length === 6)
            ? String(authRes.demo_otp)
            : Math.floor(100000 + Math.random() * 900000).toString();
          setOtpTargetEmail(authRes.otp_sent_to || email);
          setDemoOTP(activeOtpCode);
          setShowOTPModal(true);
          sendOTPEmail({ toEmail: authRes.otp_sent_to || email, toName: fullName, otpCode: activeOtpCode })
            .then((res) => console.log("[SignUp EmailJS OTP]", res))
            .catch((err) => console.warn("[SignUp EmailJS OTP Error]", err));
          setLoading(false);
          return;
        }

        sendAuthEmail({ toEmail: email, toName: fullName, actionType: "signup" }).catch(() => {});
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  // Handle OTP Submission for First-Time Users
  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      const res = await api.verifyOTP({ email: otpTargetEmail, otp: otpCodeInput });
      if (res.access_token) {
        setSuccessMsg("Email successfully verified! Redirecting to dashboard...");
        setTimeout(() => router.push("/dashboard"), 600);
      }
    } catch (err: any) {
      setError(err.message || "Invalid or expired OTP verification code.");
    } finally {
      setLoading(false);
    }
  };

  // Handle Resend OTP Request
  const handleResendOTP = async () => {
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      const res = await api.resendOTP({ email: otpTargetEmail });
      const activeOtpCode = (res.demo_otp && String(res.demo_otp).length === 6)
        ? String(res.demo_otp)
        : Math.floor(100000 + Math.random() * 900000).toString();
      setDemoOTP(activeOtpCode);
      setSuccessMsg(`Fresh 6-digit OTP code dispatched to ${otpTargetEmail}`);
      sendOTPEmail({ toEmail: otpTargetEmail, otpCode: activeOtpCode }).catch(() => {});
    } catch (err: any) {
      setError(err.message || "Failed to resend OTP code.");
    } finally {
      setLoading(false);
    }
  };

  // Google OAuth 2.0 Login via Firebase
  const handleGoogleLogin = async () => {
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    try {
      googleProvider.setCustomParameters({ prompt: "select_account" });
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;

      const fullName = user.displayName || "Google User";
      const userEmail = user.email || "user@google.com";

      // Authenticate or auto-register Google account in backend database
      const authRes = await api.googleAuth({ email: userEmail, name: fullName });
      
      if (authRes.require_otp) {
        const activeOtpCode = (authRes.demo_otp && String(authRes.demo_otp).length === 6)
          ? String(authRes.demo_otp)
          : Math.floor(100000 + Math.random() * 900000).toString();
        setOtpTargetEmail(authRes.otp_sent_to || userEmail);
        setDemoOTP(activeOtpCode);
        setShowOTPModal(true);
        sendOTPEmail({ toEmail: authRes.otp_sent_to || userEmail, toName: fullName, otpCode: activeOtpCode })
          .then((res) => console.log("[Google EmailJS OTP]", res))
          .catch((err) => console.warn("[Google EmailJS OTP Error]", err));
        setLoading(false);
        return;
      }

      router.push("/dashboard");
    } catch (err: any) {
      console.warn("Google OAuth error:", err);
      if (err.code === "auth/popup-closed-by-user") {
        setError("Google sign-in popup was closed before completion.");
      } else if (
        err.code === "auth/configuration-not-found" ||
        err.code === "auth/api-key-not-valid" ||
        err.code === "auth/invalid-api-key" ||
        err.message?.includes("configuration-not-found")
      ) {
        setError("Google OAuth Sign-In is not enabled in Firebase Console. Please use email & password above, or sign in with the Demo Account (inventor@startup.com).");
      } else {
        setError(err.message || "Google sign-in failed. Please check your network or try email login.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070815] text-zinc-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white relative overflow-hidden">
      
      {/* Background Neon Gradient Aura Rings */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[650px] bg-gradient-to-tr from-indigo-600/20 via-purple-600/15 to-cyan-500/20 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />

      <main className="flex-1 flex items-center justify-center p-4 py-12 z-10">
        
        {/* Glassmorphic Auth Card */}
        <div className="w-full max-w-md p-8 rounded-[32px] bg-[#0c0e24]/85 backdrop-blur-2xl border border-indigo-500/20 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9),0_0_30px_rgba(99,102,241,0.15)] relative">
          
          {/* Top Bar: Switcher & Close Icon */}
          <div className="flex items-center justify-between mb-8">
            
            {/* Sign up / Sign in Switcher Pill */}
            <div className="bg-[#070919] p-1 rounded-full border border-white/10 inline-flex items-center gap-1">
              <button
                type="button"
                onClick={() => { setMode("signup"); setError(null); setSuccessMsg(null); }}
                className={`px-5 py-2 rounded-full text-xs transition-all ${
                  mode === "signup"
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold shadow-lg"
                    : "text-zinc-400 hover:text-white font-medium"
                }`}
              >
                Sign up
              </button>

              <button
                type="button"
                onClick={() => { setMode("signin"); setError(null); setSuccessMsg(null); }}
                className={`px-5 py-2 rounded-full text-xs transition-all ${
                  mode === "signin"
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold shadow-lg"
                    : "text-zinc-400 hover:text-white font-medium"
                }`}
              >
                Sign in
              </button>
            </div>

            {/* Close to Home Button */}
            <Link
              href="/"
              className="w-9 h-9 rounded-full bg-white/5 hover:bg-white/15 text-white flex items-center justify-center transition-all border border-white/10"
              title="Close to Home"
            >
              <X className="w-4 h-4" />
            </Link>
          </div>

          {/* OTP Verification Modal View */}
          {showOTPModal ? (
            <div className="space-y-5 animate-in fade-in zoom-in-95 duration-200">
              <div className="text-center space-y-1.5">
                <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center justify-center mx-auto mb-2 shadow-inner">
                  <KeyRound className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-extrabold text-white">First-Time Email Verification</h2>
                <p className="text-xs text-zinc-400">
                  Enter the 6-digit OTP code sent via EmailJS to <br />
                  <span className="text-indigo-300 font-mono font-semibold">{otpTargetEmail}</span>
                </p>
              </div>

              {/* Error Banner */}
              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
                  <span>{error}</span>
                </div>
              )}

              {/* Success Banner */}
              {successMsg && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 flex-shrink-0 text-emerald-400" />
                  <span>{successMsg}</span>
                </div>
              )}

              {/* Live Verification OTP Banner (Dispatched via EmailJS & displayed for immediate testing) */}
              {demoOTP && (
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200 text-xs flex flex-col items-center gap-1.5 text-center backdrop-blur-md">
                  <span className="text-[11px] text-zinc-400 font-medium">Your 6-Digit Verification Code (Sent via EmailJS):</span>
                  <span className="text-2xl font-mono font-extrabold tracking-[0.4em] text-cyan-300 bg-[#070919] px-5 py-1.5 rounded-lg border border-cyan-500/40 shadow-inner">
                    {demoOTP}
                  </span>
                  <button
                    type="button"
                    onClick={() => setOtpCodeInput(demoOTP)}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 underline font-mono font-medium transition-colors cursor-pointer mt-0.5"
                  >
                    Click to auto-fill code ({demoOTP})
                  </button>
                </div>
              )}

              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div>
                  <input
                    type="text"
                    maxLength={6}
                    required
                    value={otpCodeInput}
                    onChange={(e) => setOtpCodeInput(e.target.value.replace(/[^0-9]/g, ''))}
                    placeholder="123456"
                    className="w-full text-center tracking-[0.5em] font-mono text-2xl bg-[#070919] border border-indigo-500/40 rounded-xl py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-indigo-400 transition-all"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || otpCodeInput.length < 6}
                  className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50 active:scale-[0.99]"
                >
                  {loading ? "Verifying OTP..." : "Verify & Complete Login"}
                </button>

                <div className="flex items-center justify-between text-xs pt-1">
                  <button
                    type="button"
                    onClick={() => { setShowOTPModal(false); setError(null); }}
                    className="text-zinc-400 hover:text-white transition-colors"
                  >
                    ← Back to Sign In
                  </button>
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    disabled={loading}
                    className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors disabled:opacity-50"
                  >
                    Resend OTP Email
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <>
              {/* Dynamic Header */}
              <div className="mb-6">
                <h2 className="text-2xl font-extrabold tracking-tight text-white">
                  {mode === "signup" ? "Create an Account" : mode === "forgot" ? "Reset Password" : "Welcome Back"}
                </h2>
                <p className="text-xs text-zinc-400 mt-1">
                  {mode === "signup"
                    ? "Sign up with Firebase to start patent prior art research"
                    : mode === "forgot"
                    ? "Enter your email to receive a password reset link"
                    : "Sign in to access your saved patent search reports"}
                </p>
              </div>

              {/* Error Banner */}
              {error && (
                <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs flex flex-col gap-2 animate-in fade-in duration-200">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-400" />
                    <span>{error}</span>
                  </div>
                  {(error.includes("Demo Account") || error.includes("Firebase")) && (
                    <button
                      type="button"
                      onClick={() => {
                        setMode("signin");
                        setEmail("inventor@startup.com");
                        setPassword("password123");
                        setError(null);
                      }}
                      className="mt-1 self-start px-3 py-1.5 rounded-lg bg-indigo-600/40 hover:bg-indigo-600/60 border border-indigo-500/50 text-indigo-200 font-mono text-[11px] transition-all flex items-center gap-1.5 shadow-sm"
                    >
                      <Sparkles className="w-3 h-3 text-indigo-300 animate-pulse" />
                      <span>Click to auto-fill Demo Credentials (inventor@startup.com)</span>
                    </button>
                  )}
                </div>
              )}

              {/* Success Banner */}
              {successMsg && (
                <div className="mb-6 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs flex items-start gap-2 animate-in fade-in duration-200">
                  <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-400" />
                  <span>{successMsg}</span>
                </div>
              )}
            </>
          )}

          {/* Main Auth Form (Hidden when OTP verification modal is active) */}
          {!showOTPModal && (
            <>
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
                      className="w-full bg-[#070919] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500/60 transition-all"
                    />
                    <input
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      placeholder="Last name"
                      className="w-full bg-[#070919] border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500/60 transition-all"
                    />
                  </div>
                )}

                {/* Email Field */}
                <div className="relative">
                  <Mail className="w-4 h-4 text-zinc-400 absolute left-4 top-3.5" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email address"
                    className="w-full bg-[#070919] border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500/60 transition-all"
                  />
                </div>

                {/* Password Field (Only for Sign In & Sign Up) */}
                {mode !== "forgot" && (
                  <div className="relative">
                    <Lock className="w-4 h-4 text-zinc-400 absolute left-4 top-3.5" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full bg-[#070919] border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500/60 transition-all"
                    />
                  </div>
                )}

                {/* Forgot Password & Quick Demo Links */}
                {mode === "signin" && (
                  <div className="flex items-center justify-between pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setEmail("inventor@startup.com");
                        setPassword("password123");
                        setError(null);
                      }}
                      className="text-xs font-mono font-medium text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1.5 cursor-pointer bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/30"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                      <span>Use Demo Account</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => { setMode("forgot"); setError(null); setSuccessMsg(null); }}
                      className="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Forgot password?
                    </button>
                  </div>
                )}

                {/* Back to Sign In Link if in Forgot Password Mode */}
                {mode === "forgot" && (
                  <div className="flex justify-end pt-1">
                    <button
                      type="button"
                      onClick={() => { setMode("signin"); setError(null); setSuccessMsg(null); }}
                      className="text-xs font-medium text-zinc-400 hover:text-white transition-colors"
                    >
                      Back to Sign In
                    </button>
                  </div>
                )}

                {/* Primary Submit Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 hover:opacity-95 text-white font-bold text-sm shadow-[0_0_25px_rgba(99,102,241,0.4)] transition-all mt-4 disabled:opacity-50 active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : mode === "signup" ? (
                    <>
                      <span>Create Account</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  ) : mode === "forgot" ? (
                    <>
                      <span>Send Reset Email</span>
                      <KeyRound className="w-4 h-4" />
                    </>
                  ) : (
                    <>
                      <span>Sign In to Account</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Social Auth Separator (Only for Sign in / Sign up) */}
              {mode !== "forgot" && (
                <>
                  <div className="relative my-6 text-center">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-white/10" />
                    </div>
                    <span className="relative px-3 bg-[#0c0e24] text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
                      OR CONTINUE WITH
                    </span>
                  </div>

                  {/* Google OAuth 2.0 Button */}
                  <button
                    type="button"
                    onClick={handleGoogleLogin}
                    disabled={loading}
                    className="w-full py-3 px-4 rounded-xl bg-[#070919] hover:bg-[#101438] border border-indigo-500/30 hover:border-indigo-500/60 flex items-center justify-center gap-3 transition-all group shadow-md cursor-pointer disabled:opacity-50"
                  >
                    <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                    </svg>
                    <span className="text-xs font-semibold text-zinc-200 group-hover:text-white">
                      Sign in with Google 
                    </span>
                  </button>
                </>
              )}
            </>
          )}

          {/* Footer Disclaimer */}
          <p className="mt-6 text-center text-xs text-zinc-500 font-normal">
            By logging in, you agree to our{" "}
            <Link href="/" className="underline text-indigo-400 hover:text-indigo-300">
              Terms & Privacy Policy
            </Link>
          </p>

        </div>
      </main>

      <footer className="py-4 text-center text-xs text-zinc-600 font-mono z-10">
        PatentLens AI • Firebase Auth & EmailJS Enabled © 2026
      </footer>
    </div>
  );
}
