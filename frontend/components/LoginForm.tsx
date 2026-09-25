"use client";

import React, { useState } from "react";
import AnimatedInput from "./AnimatedInput";
import LoginButton from "./LoginButton";
import LoginFeedback from "./LoginFeedback";

interface LoginFormProps {
  mode: "signin" | "signup" | "forgot";
  setMode: (mode: "signin" | "signup" | "forgot") => void;
  email: string;
  setEmail: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  firstName: string;
  setFirstName: (val: string) => void;
  lastName: string;
  setLastName: (val: string) => void;
  rememberMe: boolean;
  setRememberMe: (val: boolean) => void;
  onFocusedFieldChange: (field: "email" | "password" | "name" | null) => void;
  onPasswordToggle: (visible: boolean) => void;
  onSubmit: (e: React.FormEvent) => void;
  onGoogleLogin: () => void;
  onFillDemo: () => void;
  loading: boolean;
  isSuccess: boolean;
  error: string | null;
  successMsg: string | null;
  showOTPModal: boolean;
  otpCodeInput: string;
  setOtpCodeInput: (val: string) => void;
  demoOTP: string | null;
  otpTargetEmail: string;
  onVerifyOTP: (e: React.FormEvent) => void;
}

export default function LoginForm({
  mode,
  setMode,
  email,
  setEmail,
  password,
  setPassword,
  firstName,
  setFirstName,
  lastName,
  setLastName,
  rememberMe,
  setRememberMe,
  onFocusedFieldChange,
  onPasswordToggle,
  onSubmit,
  onGoogleLogin,
  onFillDemo,
  loading,
  isSuccess,
  error,
  successMsg,
  showOTPModal,
  otpCodeInput,
  setOtpCodeInput,
  demoOTP,
  otpTargetEmail,
  onVerifyOTP,
}: LoginFormProps) {
  return (
    <div className="w-full flex flex-col justify-between h-full">
      {/* Top Header Section */}
      <div className="space-y-4">
        {/* Brand Logo & Demo Filler Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center text-lg font-black shadow-sm">
              ✦
            </div>
            <span className="font-extrabold text-sm text-slate-900 tracking-tight">
              PatentLens AI
            </span>
          </div>

          <button
            type="button"
            onClick={onFillDemo}
            className="text-xs font-semibold text-purple-600 hover:text-purple-700 bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-full transition-colors cursor-pointer"
          >
            ⚡ Fill Demo
          </button>
        </div>

        {/* Heading & Supporting Text */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            {mode === "signup"
              ? "Create an Account"
              : mode === "forgot"
              ? "Reset Password"
              : "Welcome Back"}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1.5 font-medium leading-relaxed">
            {mode === "signup"
              ? "Start your AI prior-art research platform."
              : mode === "forgot"
              ? "Enter your email address to receive password reset instructions."
              : "Sign in to continue your learning journey."}
          </p>
        </div>

        {/* Inline Feedback Banner */}
        <LoginFeedback error={error} success={successMsg} />
      </div>

      {/* Form Fields Section */}
      <div className="my-6">
        {showOTPModal ? (
          <form onSubmit={onVerifyOTP} className="space-y-4">
            <p className="text-xs text-slate-600">
              Enter the 6-digit verification code sent to{" "}
              <span className="font-bold text-slate-900">{otpTargetEmail}</span>
            </p>
            {demoOTP && (
              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-mono">
                Demo OTP Code: <strong className="text-amber-900">{demoOTP}</strong>
              </div>
            )}
            <input
              type="text"
              maxLength={6}
              required
              value={otpCodeInput}
              onChange={(e) => setOtpCodeInput(e.target.value.replace(/[^0-9]/g, ""))}
              placeholder="123456"
              className="w-full text-center tracking-[0.5em] font-mono text-xl py-3 border-2 border-slate-200 rounded-xl focus:outline-none focus:border-slate-900"
            />
            <LoginButton
              label="Verify & Complete Login"
              loading={loading}
              success={isSuccess}
              disabled={otpCodeInput.length < 6}
            />
          </form>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            {/* Sign Up Fields */}
            {mode === "signup" && (
              <div className="grid grid-cols-2 gap-3">
                <AnimatedInput
                  id="firstName"
                  label="First Name"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  onFocus={() => onFocusedFieldChange("name")}
                  onBlur={() => onFocusedFieldChange(null)}
                  placeholder="Anna"
                />
                <AnimatedInput
                  id="lastName"
                  label="Last Name"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  onFocus={() => onFocusedFieldChange("name")}
                  onBlur={() => onFocusedFieldChange(null)}
                  placeholder="Smith"
                />
              </div>
            )}

            {/* Email Input */}
            <AnimatedInput
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={() => onFocusedFieldChange("email")}
              onBlur={() => onFocusedFieldChange(null)}
              placeholder="anna@gmail.com"
            />

            {/* Password Input */}
            {mode !== "forgot" && (
              <AnimatedInput
                id="password"
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={() => onFocusedFieldChange("password")}
                onBlur={() => onFocusedFieldChange(null)}
                placeholder="••••••••"
                showPasswordToggle={true}
                onTogglePassword={onPasswordToggle}
              />
            )}

            {/* Remember Me & Forgot Password Links */}
            {mode === "signin" && (
              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-slate-600 hover:text-slate-900 select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded-sm border-slate-300 text-slate-900 focus:ring-slate-900 accent-slate-900 cursor-pointer"
                  />
                  <span>Remember me</span>
                </label>

                <button
                  type="button"
                  onClick={() => setMode("forgot")}
                  className="text-slate-500 hover:text-slate-900 font-medium transition-colors cursor-pointer"
                >
                  Forgot password?
                </button>
              </div>
            )}

            {/* Primary Action Button */}
            <div className="pt-2">
              <LoginButton
                label={
                  mode === "signup"
                    ? "Create Account"
                    : mode === "forgot"
                    ? "Send Password Reset Link"
                    : "Sign In"
                }
                loading={loading}
                success={isSuccess}
              />
            </div>

            {/* Google OAuth Button */}
            {mode !== "forgot" && (
              <button
                type="button"
                onClick={onGoogleLogin}
                disabled={loading}
                className="w-full py-3.5 px-4 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs sm:text-sm flex items-center justify-center gap-2.5 transition-all cursor-pointer shadow-xs border border-slate-200/80 active:scale-[0.99] disabled:opacity-50"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>Log in with Google</span>
              </button>
            )}
          </form>
        )}
      </div>

      {/* Footer Mode Switcher */}
      <div className="pt-2 text-center text-xs text-slate-500 font-medium">
        {mode === "signin" ? (
          <p>
            Don't have an account?{" "}
            <button
              type="button"
              onClick={() => setMode("signup")}
              className="font-bold text-slate-900 hover:underline transition-all cursor-pointer"
            >
              Create account
            </button>
          </p>
        ) : (
          <p>
            Already have an account?{" "}
            <button
              type="button"
              onClick={() => setMode("signin")}
              className="font-bold text-slate-900 hover:underline transition-all cursor-pointer"
            >
              Sign In
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
