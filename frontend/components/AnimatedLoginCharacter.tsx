"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useReducedMotion } from "framer-motion";

export type AnimationState =
  | "IDLE"
  | "EMAIL_FOCUS"
  | "PASSWORD_FOCUS"
  | "PASSWORD_VISIBLE"
  | "LOADING"
  | "ERROR"
  | "SUCCESS";

interface AnimatedLoginCharacterProps {
  state: AnimationState;
}

export default function AnimatedLoginCharacter({
  state,
}: AnimatedLoginCharacterProps) {
  const shouldReduceMotion = useReducedMotion();
  const containerRef = useRef<HTMLDivElement>(null);

  // Mouse position state for real-time eye cursor tracking during IDLE state
  const [mousePupilPos, setMousePupilPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Listen to mouse movement across the page to track cursor when outside input fields
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (state !== "IDLE") return;

      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        const deltaX = e.clientX - centerX;
        const deltaY = e.clientY - centerY;

        const maxDistX = Math.max(window.innerWidth / 2, 300);
        const maxDistY = Math.max(window.innerHeight / 2, 300);

        const pupilX = Math.min(Math.max((deltaX / maxDistX) * 9, -7), 7);
        const pupilY = Math.min(Math.max((deltaY / maxDistY) * 5, -5), 5);

        setMousePupilPos({ x: pupilX, y: pupilY });
      } else {
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const deltaX = e.clientX - centerX;
        const deltaY = e.clientY - centerY;

        const pupilX = Math.min(Math.max((deltaX / centerX) * 8, -7), 7);
        const pupilY = Math.min(Math.max((deltaY / centerY) * 5, -5), 5);

        setMousePupilPos({ x: pupilX, y: pupilY });
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [state]);

  // Head & Body Lean / Tilt based on state
  const getBodyTransform = () => {
    if (shouldReduceMotion) return { x: 0, y: 0, rotate: 0 };
    switch (state) {
      case "EMAIL_FOCUS":
        return { x: 8, y: 2, rotate: 4 };
      case "PASSWORD_FOCUS":
        return { x: -4, y: 4, rotate: -4 };
      case "PASSWORD_VISIBLE":
        return { x: 4, y: -2, rotate: 2 };
      case "LOADING":
        return { x: 0, y: 4, rotate: 0 };
      case "ERROR":
        return { x: -8, y: 2, rotate: -6 };
      case "SUCCESS":
        return { x: 0, y: -12, rotate: 0 };
      case "IDLE":
      default:
        return { x: 0, y: 0, rotate: 0 };
    }
  };

  // Eye Pupil Movement Coordinates
  const getPupilCoordinates = () => {
    switch (state) {
      case "EMAIL_FOCUS":
        return { x: 7, y: 2 }; // Looking towards email field on right
      case "PASSWORD_FOCUS":
        return { x: -6, y: -4 }; // Looking away top-left for privacy
      case "PASSWORD_VISIBLE":
        return { x: 6, y: 2 }; // Peeking right at visible password
      case "LOADING":
        return { x: 0, y: 3 };
      case "ERROR":
        return { x: -3, y: -4 };
      case "SUCCESS":
        return { x: 2, y: -3 };
      case "IDLE":
      default:
        return mousePupilPos; // Real-time cursor tracking!
    }
  };

  // Hands Position for PASSWORD_FOCUS
  const getLeftHandPosition = () => {
    if (shouldReduceMotion) return { x: 0, y: 0 };
    switch (state) {
      case "PASSWORD_FOCUS":
        return { x: 38, y: -54, rotate: -30, scale: 1.1 };
      case "PASSWORD_VISIBLE":
        return { x: 35, y: -30, rotate: -15, scale: 1.0 };
      case "SUCCESS":
        return { x: -20, y: -65, rotate: -45, scale: 1.1 };
      case "ERROR":
        return { x: 10, y: -15, rotate: 15, scale: 1 };
      case "IDLE":
      case "EMAIL_FOCUS":
      case "LOADING":
      default:
        return { x: 0, y: 0, rotate: 0, scale: 0 };
    }
  };

  const getRightHandPosition = () => {
    if (shouldReduceMotion) return { x: 0, y: 0 };
    switch (state) {
      case "PASSWORD_FOCUS":
        return { x: -38, y: -54, rotate: 30, scale: 1.1 };
      case "PASSWORD_VISIBLE":
        return { x: -35, y: -30, rotate: 15, scale: 1.0 };
      case "SUCCESS":
        return { x: 20, y: -65, rotate: 45, scale: 1.1 };
      case "ERROR":
        return { x: -10, y: -15, rotate: -15, scale: 1 };
      case "IDLE":
      case "EMAIL_FOCUS":
      case "LOADING":
      default:
        return { x: 0, y: 0, rotate: 0, scale: 0 };
    }
  };

  const bodyTransform = getBodyTransform();
  const pupilPos = getPupilCoordinates();
  const leftHand = getLeftHandPosition();
  const rightHand = getRightHandPosition();

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[380px] sm:min-h-[460px] bg-[#e5e7eb] rounded-3xl lg:rounded-r-none p-4 sm:p-8 flex flex-col items-center justify-center overflow-hidden selection:bg-purple-200"
    >
      {/* Floating Sparkles & Particles on SUCCESS */}
      {state === "SUCCESS" && (
        <div className="absolute inset-0 pointer-events-none z-30">
          {[...Array(10)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-3 h-3 rounded-full"
              style={{
                backgroundColor: ["#ff6b2c", "#6b26ff", "#ffcc00", "#10b981", "#3b82f6"][i % 5],
                left: `${15 + i * 8}%`,
                top: `${45 + (i % 3) * 8}%`,
              }}
              initial={{ scale: 0, opacity: 1, y: 0 }}
              animate={{
                scale: [0, 1.3, 0.8],
                opacity: [1, 1, 0],
                y: -70 - i * 12,
                x: (i % 2 === 0 ? 1 : -1) * (25 + i * 6),
              }}
              transition={{ duration: 1, delay: i * 0.06 }}
            />
          ))}
        </div>
      )}

      {/* Layered Interactive Character Artwork matching reference image exactly */}
      <motion.div
        className="relative w-full max-w-[340px] sm:max-w-[420px] aspect-[4/3] flex items-end justify-center"
        animate={{
          x: bodyTransform.x,
          y: bodyTransform.y,
          rotate: bodyTransform.rotate,
        }}
        transition={{ type: "spring", stiffness: 220, damping: 20 }}
      >
        {/* 1. PURPLE TALL RECTANGLE (Very Tall, Sharp Corners, Vertical Nose Line) */}
        <motion.div
          className="absolute left-[27%] bottom-0 w-[30%] h-[85%] rounded-none bg-[#6b26ff] flex flex-col items-center pt-4 z-10"
          animate={
            shouldReduceMotion
              ? {}
              : {
                  y: state === "SUCCESS" ? [-4, -18, -4] : state === "IDLE" ? [0, -4, 0] : 0,
                }
          }
          transition={{
            duration: state === "SUCCESS" ? 0.6 : 3,
            repeat: state === "IDLE" ? Infinity : 0,
            ease: "easeInOut",
          }}
        >
          {/* Eyes near top edge */}
          <div className="flex gap-4 items-center mt-1 relative">
            {state === "PASSWORD_FOCUS" ? (
              <div className="flex gap-4 text-slate-950 font-black text-xs">
                <span>⌒</span>
                <span>⌒</span>
              </div>
            ) : (
              <>
                <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center relative overflow-hidden">
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full bg-[#18181b]"
                    animate={{ x: pupilPos.x, y: pupilPos.y }}
                    transition={{ type: "spring", stiffness: 350, damping: 22 }}
                  />
                </div>
                <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center relative overflow-hidden">
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full bg-[#18181b]"
                    animate={{ x: pupilPos.x, y: pupilPos.y }}
                    transition={{ type: "spring", stiffness: 350, damping: 22 }}
                  />
                </div>
              </>
            )}
          </div>

          {/* Vertical Nose/Mouth Line directly centered between eyes */}
          <div className="mt-1.5 flex flex-col items-center">
            {state === "ERROR" ? (
              <div className="w-3.5 h-1.5 bg-[#18181b] rounded-full" />
            ) : state === "SUCCESS" ? (
              <div className="w-3.5 h-2 bg-white rounded-b-full" />
            ) : (
              <div className="w-1.5 h-7 bg-[#18181b] rounded-xs" />
            )}
          </div>
        </motion.div>

        {/* 2. BLACK RECTANGLE PILLAR (Sharp Corners, Peeking Eyes Protruding past Upper Right Edge) */}
        <motion.div
          className="absolute left-[51%] bottom-0 w-[22%] h-[58%] rounded-none bg-[#18181b] flex flex-col items-end pr-1 pt-6 z-15 overflow-visible"
          animate={
            shouldReduceMotion
              ? {}
              : {
                  y: state === "SUCCESS" ? [-3, -14, -3] : state === "IDLE" ? [0, -3, 0] : 0,
                  scaleY: state === "PASSWORD_FOCUS" ? 0.95 : 1,
                }
          }
          transition={{
            duration: state === "IDLE" ? 3.5 : 0.3,
            repeat: state === "IDLE" ? Infinity : 0,
            ease: "easeInOut",
          }}
        >
          {/* Eyes peeking out upper right edge */}
          <div className="flex gap-1 items-center relative -right-2.5 top-0">
            {state === "PASSWORD_FOCUS" ? (
              <div className="flex gap-2 text-white text-xs font-bold">
                <span>⌒</span>
                <span>⌒</span>
              </div>
            ) : (
              <>
                <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center relative overflow-hidden">
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full bg-[#18181b]"
                    animate={{ x: pupilPos.x * 0.8, y: pupilPos.y * 0.8 }}
                    transition={{ type: "spring", stiffness: 350, damping: 22 }}
                  />
                </div>
                <div className="w-4 h-4 rounded-full bg-white flex items-center justify-center relative overflow-hidden">
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full bg-[#18181b]"
                    animate={{ x: pupilPos.x * 0.8, y: pupilPos.y * 0.8 }}
                    transition={{ type: "spring", stiffness: 350, damping: 22 }}
                  />
                </div>
              </>
            )}
          </div>
        </motion.div>

        {/* 3. ORANGE DOME BLOB (Clean Smooth Semi-Circle Dome, No Extra Hand Ball) */}
        <motion.div
          className="absolute left-[8%] bottom-0 w-[50%] h-[44%] rounded-t-[200px] bg-[#ff6b2c] flex flex-col items-center justify-center z-20 relative"
          animate={
            shouldReduceMotion
              ? {}
              : {
                  x: state === "EMAIL_FOCUS" ? 12 : state === "ERROR" ? -8 : 0,
                  y: state === "SUCCESS" ? [-4, -16, -4] : state === "IDLE" ? [0, -5, 0] : 0,
                }
          }
          transition={{
            duration: state === "IDLE" ? 2.8 : 0.3,
            repeat: state === "IDLE" ? Infinity : 0,
            ease: "easeInOut",
          }}
        >
          {/* Animated Hands (Only during PASSWORD_FOCUS protection gesture) */}
          <motion.div
            className="absolute left-2 top-8 w-5 h-5 rounded-full bg-[#ff6b2c] border-2 border-slate-900/20 shadow-md z-30"
            animate={{
              x: leftHand.x,
              y: leftHand.y,
              rotate: leftHand.rotate,
              scale: leftHand.scale,
            }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          />
          <motion.div
            className="absolute right-2 top-8 w-5 h-5 rounded-full bg-[#ff6b2c] border-2 border-slate-900/20 shadow-md z-30"
            animate={{
              x: rightHand.x,
              y: rightHand.y,
              rotate: rightHand.rotate,
              scale: rightHand.scale,
            }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          />

          {/* Orange Face */}
          <div className="flex flex-col items-center mt-3">
            <div className="flex gap-7 items-center">
              {state === "PASSWORD_FOCUS" ? (
                <div className="flex gap-5 text-slate-950 font-bold text-sm">
                  <span>⌒</span>
                  <span>⌒</span>
                </div>
              ) : (
                <>
                  <div className="w-3.5 h-3.5 rounded-full bg-[#18181b] relative overflow-hidden">
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-white absolute top-0.5 right-0.5"
                      animate={{ x: pupilPos.x * 0.3, y: pupilPos.y * 0.3 }}
                      transition={{ type: "spring", stiffness: 350, damping: 22 }}
                    />
                  </div>
                  <div className="w-3.5 h-3.5 rounded-full bg-[#18181b] relative overflow-hidden">
                    <motion.div
                      className="w-1.5 h-1.5 rounded-full bg-white absolute top-0.5 right-0.5"
                      animate={{ x: pupilPos.x * 0.3, y: pupilPos.y * 0.3 }}
                      transition={{ type: "spring", stiffness: 350, damping: 22 }}
                    />
                  </div>
                </>
              )}
            </div>

            {/* Happy Semi-Circle Mouth */}
            <div className="mt-1.5">
              {state === "ERROR" ? (
                <div className="w-4 h-1.5 border-t-2 border-[#18181b] rounded-full" />
              ) : (
                <div className="w-4 h-2 bg-[#18181b] rounded-b-full" />
              )}
            </div>
          </div>
        </motion.div>


      </motion.div>

    </div>
  );
}
