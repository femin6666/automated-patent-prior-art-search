"use client";

import { motion } from "framer-motion";

export type AuthInteractionState =
  | "idle"
  | "emailFocused"
  | "passwordFocused"
  | "passwordVisible"
  | "typing"
  | "loading"
  | "error"
  | "success";

interface AnimatedLoginIllustrationProps {
  authState: AuthInteractionState;
  emailLength?: number;
}

export default function AnimatedLoginIllustration({
  authState,
  emailLength = 0,
}: AnimatedLoginIllustrationProps) {

  // Dynamic eye pupil offset calculation for tracking text input length
  const getEyeOffset = () => {
    if (authState === "emailFocused" || authState === "typing") {
      const x = Math.min(emailLength * 0.5, 9) + 4;
      const y = 2;
      return { x, y };
    }
    if (authState === "passwordFocused") {
      return { x: -6, y: -4 }; // looking away top-left
    }
    if (authState === "passwordVisible") {
      return { x: 8, y: 3 }; // peeking right with wide eyes
    }
    if (authState === "error") {
      return { x: -2, y: -3 }; // looking up worried
    }
    if (authState === "success") {
      return { x: 3, y: -2 }; // happy looking up
    }
    return { x: 0, y: 0 };
  };

  const eyeOffset = getEyeOffset();

  // Character tilt angles based on state
  const purpleTilt =
    authState === "emailFocused" || authState === "typing"
      ? 9
      : authState === "error"
      ? -10
      : authState === "success"
      ? -4
      : 0;

  const orangeShiftX =
    authState === "emailFocused" || authState === "typing"
      ? 12
      : authState === "error"
      ? -8
      : 0;

  const yellowTilt =
    authState === "passwordFocused"
      ? -12
      : authState === "emailFocused" || authState === "typing"
      ? 6
      : authState === "error"
      ? 8
      : 0;

  return (
    <div className="relative w-full h-full min-h-[380px] sm:min-h-[460px] bg-[#eef0f3] rounded-3xl lg:rounded-r-none p-6 sm:p-10 flex flex-col items-center justify-center overflow-hidden selection:bg-purple-200">
      


      {/* Floating Sparkles & Particles on Success */}
      {authState === "success" && (
        <div className="absolute inset-0 pointer-events-none z-20">
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-3 h-3 rounded-full"
              style={{
                backgroundColor: ["#ff6b2c", "#6b26ff", "#ffcc00", "#10b981"][i % 4],
                left: `${20 + i * 10}%`,
                top: `${40 + (i % 3) * 10}%`,
              }}
              initial={{ scale: 0, opacity: 1, y: 0 }}
              animate={{
                scale: [0, 1.2, 0.8],
                opacity: [1, 1, 0],
                y: -60 - i * 10,
                x: (i % 2 === 0 ? 1 : -1) * (20 + i * 5),
              }}
              transition={{ duration: 1, delay: i * 0.08 }}
            />
          ))}
        </div>
      )}

      {/* Main Characters Assembly SVG */}
      <div className="relative w-full max-w-[340px] sm:max-w-[400px] aspect-[4/3] flex items-end justify-center">
        
        {/* 1. PURPLE TALL CHARACTER (Back Left) */}
        <motion.div
          className="absolute left-[18%] bottom-[12%] w-[28%] h-[64%] rounded-t-3xl bg-[#6b26ff] shadow-lg flex flex-col items-center pt-6 z-10"
          animate={{
            rotate: purpleTilt,
            y: authState === "success" ? [-5, -18, -5] : authState === "idle" ? [0, -4, 0] : 0,
          }}
          transition={{
            duration: authState === "success" ? 0.6 : 3,
            repeat: authState === "idle" ? Infinity : 0,
            ease: "easeInOut",
          }}
        >
          {/* Eyes */}
          <div className="flex gap-4 items-center mt-2">
            {/* Left Eye */}
            <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-white flex items-center justify-center relative overflow-hidden shadow-sm">
              <motion.div
                className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-slate-950"
                animate={{ x: eyeOffset.x, y: eyeOffset.y }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              />
            </div>
            {/* Right Eye */}
            <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-white flex items-center justify-center relative overflow-hidden shadow-sm">
              <motion.div
                className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-slate-950"
                animate={{ x: eyeOffset.x, y: eyeOffset.y }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              />
            </div>
          </div>

          {/* Mouth */}
          <div className="mt-3">
            {authState === "error" ? (
              // Frown
              <svg className="w-6 h-3 text-slate-950 stroke-current" viewBox="0 0 24 12" fill="none" strokeWidth="3" strokeLinecap="round">
                <path d="M 4 10 Q 12 2 20 10" />
              </svg>
            ) : authState === "success" ? (
              // Happy Smile
              <svg className="w-6 h-3 text-white stroke-current" viewBox="0 0 24 12" fill="none" strokeWidth="3" strokeLinecap="round">
                <path d="M 4 2 Q 12 10 20 2" />
              </svg>
            ) : (
              // Neutral / Small Mouth
              <div className="w-4 h-1.5 bg-slate-950 rounded-full" />
            )}
          </div>
        </motion.div>

        {/* 2. BLACK RECTANGLE PILLAR (Center Back) */}
        <motion.div
          className="absolute left-[44%] bottom-[12%] w-[20%] h-[48%] rounded-t-xl bg-[#18181b] shadow-md flex flex-col items-center pt-4 z-15"
          animate={{
            y: authState === "success" ? [-3, -12, -3] : authState === "idle" ? [0, -3, 0] : 0,
            scaleY: authState === "passwordFocused" ? 0.95 : 1,
          }}
          transition={{
            duration: authState === "idle" ? 3.5 : 0.3,
            repeat: authState === "idle" ? Infinity : 0,
            ease: "easeInOut",
          }}
        >
          {/* Eyes */}
          <div className="flex gap-2.5 items-center mt-1">
            {authState === "passwordFocused" ? (
              // Covered / Closed Eyes
              <div className="flex gap-2 text-white text-xs font-bold">
                <span>⌒</span>
                <span>⌒</span>
              </div>
            ) : (
              <>
                <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center relative overflow-hidden">
                  <motion.div
                    className="w-2 h-2 rounded-full bg-slate-950"
                    animate={{ x: eyeOffset.x * 0.8, y: eyeOffset.y * 0.8 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  />
                </div>
                <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center relative overflow-hidden">
                  <motion.div
                    className="w-2 h-2 rounded-full bg-slate-950"
                    animate={{ x: eyeOffset.x * 0.8, y: eyeOffset.y * 0.8 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  />
                </div>
              </>
            )}
          </div>
        </motion.div>

        {/* 3. ORANGE DOME BLOB (Front Left) */}
        <motion.div
          className="absolute left-[5%] bottom-[12%] w-[48%] h-[42%] rounded-t-[90px] bg-[#ff6b2c] shadow-xl flex flex-col items-center justify-center z-20"
          animate={{
            x: orangeShiftX,
            y: authState === "success" ? [-4, -16, -4] : authState === "idle" ? [0, -5, 0] : 0,
          }}
          transition={{
            duration: authState === "idle" ? 2.8 : 0.3,
            repeat: authState === "idle" ? Infinity : 0,
            ease: "easeInOut",
          }}
        >
          {/* Face */}
          <div className="flex flex-col items-center -mt-2">
            {/* Eyes */}
            <div className="flex gap-6 items-center">
              {authState === "passwordFocused" ? (
                // Closed Eye Arcs
                <div className="flex gap-5 text-slate-950 font-bold text-sm">
                  <span>⌒</span>
                  <span>⌒</span>
                </div>
              ) : (
                <>
                  <div className="w-3.5 h-3.5 sm:w-4 sm:h-4 rounded-full bg-slate-950 relative overflow-hidden">
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-white absolute top-0.5 right-0.5"
                      animate={{ x: eyeOffset.x * 0.3, y: eyeOffset.y * 0.3 }}
                    />
                  </div>
                  <div className="w-3.5 h-3.5 sm:w-4 sm:h-4 rounded-full bg-slate-950 relative overflow-hidden">
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-white absolute top-0.5 right-0.5"
                      animate={{ x: eyeOffset.x * 0.3, y: eyeOffset.y * 0.3 }}
                    />
                  </div>
                </>
              )}
            </div>

            {/* Mouth */}
            <div className="mt-2">
              {authState === "error" ? (
                <div className="w-4 h-1.5 border-t-2 border-slate-950 rounded-full" />
              ) : authState === "success" ? (
                <div className="w-5 h-2.5 border-b-2 border-slate-950 rounded-full" />
              ) : (
                <div className="w-3.5 h-1.5 border-b-2 border-slate-950 rounded-full" />
              )}
            </div>
          </div>
        </motion.div>



      </div>

      {/* Subtitle / Interaction Helper Tag */}
      <div className="mt-6 text-center z-20">
        <motion.span
          className="text-xs font-mono font-medium text-slate-500 tracking-wide inline-block px-3 py-1 rounded-full bg-white/60 border border-slate-200/80 shadow-xs"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {authState === "emailFocused"
            ? "👀 Watching your email input..."
            : authState === "passwordFocused"
            ? "🙈 Privacy mode active!"
            : authState === "passwordVisible"
            ? "👁 Peeking password..."
            : authState === "error"
            ? "⚠️ Authentication error detected"
            : authState === "success"
            ? "🎉 Welcome back, Innovator!"
            : "✨ Interactive Learning Platform"}
        </motion.span>
      </div>

    </div>
  );
}
