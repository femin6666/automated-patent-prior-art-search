"use client";

import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

interface AnimatedInputProps {
  id: string;
  label: string;
  type: string;
  value: string;
  placeholder?: string;
  required?: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  showPasswordToggle?: boolean;
  onTogglePassword?: (isVisible: boolean) => void;
}

export default function AnimatedInput({
  id,
  label,
  type,
  value,
  placeholder = "",
  required = true,
  onChange,
  onFocus,
  onBlur,
  showPasswordToggle = false,
  onTogglePassword,
}: AnimatedInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const handleFocus = () => {
    setIsFocused(true);
    if (onFocus) onFocus();
  };

  const handleBlur = () => {
    setIsFocused(false);
    if (onBlur) onBlur();
  };

  const togglePasswordVisibility = () => {
    const nextState = !isPasswordVisible;
    setIsPasswordVisible(nextState);
    if (onTogglePassword) {
      onTogglePassword(nextState);
    }
  };

  const currentType = showPasswordToggle
    ? isPasswordVisible
      ? "text"
      : "password"
    : type;

  return (
    <div className="space-y-1.5 text-left w-full">
      <label
        htmlFor={id}
        className="block text-xs font-semibold text-slate-700 tracking-tight"
      >
        {label}
      </label>

      <div className="relative flex items-center">
        <input
          id={id}
          type={currentType}
          required={required}
          value={value}
          onChange={onChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          className={`w-full py-3 px-4 bg-slate-50/80 border text-slate-900 text-sm font-medium rounded-xl transition-all duration-200 placeholder:text-slate-400 focus:outline-none ${
            isFocused
              ? "border-indigo-600 bg-white ring-3 ring-indigo-500/10 shadow-xs"
              : "border-slate-200/90 hover:border-slate-300"
          }`}
        />

        {showPasswordToggle && (
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute right-3.5 p-1.5 text-slate-400 hover:text-slate-700 transition-colors focus:outline-none rounded-lg"
            title={isPasswordVisible ? "Hide password" : "Show password"}
            aria-label={isPasswordVisible ? "Hide password" : "Show password"}
          >
            {isPasswordVisible ? (
              <EyeOff className="w-4 h-4 text-slate-700" />
            ) : (
              <Eye className="w-4 h-4 text-slate-400" />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
