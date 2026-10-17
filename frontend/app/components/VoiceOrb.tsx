"use client";

import React from "react";
import { Microphone, MicrophoneSlash, Sparkle } from "@phosphor-icons/react";

interface VoiceOrbProps {
  state: "listening" | "thinking" | "speaking";
  isMuted: boolean;
  onToggleMute: () => void;
  onClickOrb?: () => void;
}

export function VoiceOrb({ state, isMuted, onToggleMute, onClickOrb }: VoiceOrbProps) {
  const getOrbClass = () => {
    if (state === "thinking") return "orb-thinking";
    if (state === "speaking") return "orb-speaking";
    return "orb-listening";
  };

  const getGradient = () => {
    if (state === "thinking") {
      return "from-[#A855F7] via-[#6366F1] to-[#3B82F6]";
    }
    if (state === "speaking") {
      return "from-[#10B981] via-[#06B6D4] to-[#3B82F6]";
    }
    return "from-[#00F0FF] via-[#0284C7] to-[#6366F1]";
  };

  return (
    <div className="relative flex flex-col items-center justify-center py-6 select-none">
      {/* Outer Glow Halo */}
      <div
        className={`absolute w-64 h-64 rounded-full blur-3xl opacity-30 transition-all duration-700 ${
          state === "thinking"
            ? "bg-[#A855F7]"
            : state === "speaking"
            ? "bg-[#10B981]"
            : "bg-[#00F0FF]"
        }`}
      />

      {/* Main Interactive Orb */}
      <div
        onClick={onClickOrb || onToggleMute}
        className={`relative w-40 h-40 md:w-48 md:h-48 rounded-full cursor-pointer flex items-center justify-center bg-gradient-to-tr ${getGradient()} ${getOrbClass()} transition-transform duration-500`}
        title={isMuted ? "Unmute microphone" : "Click to interact"}
      >
        {/* Core highlight */}
        <div className="absolute inset-2 rounded-full bg-gradient-to-b from-white/30 via-transparent to-black/40 pointer-events-none" />

        {/* Center state icon */}
        <div className="relative z-10 flex flex-col items-center justify-center text-white drop-shadow-md">
          {isMuted ? (
            <MicrophoneSlash size={36} weight="duotone" className="text-rose-300" />
          ) : state === "thinking" ? (
            <Sparkle size={38} weight="fill" className="text-amber-200 animate-spin" />
          ) : (
            <Microphone size={36} weight="duotone" className="text-white" />
          )}
        </div>
      </div>

      {/* Status Label */}
      <div className="mt-5 flex items-center gap-2">
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            state === "thinking"
              ? "bg-[#A855F7] animate-ping"
              : state === "speaking"
              ? "bg-[#10B981] animate-pulse"
              : "bg-[#00F0FF] animate-pulse"
          }`}
        />
        <span className="text-xs uppercase tracking-widest font-mono text-slate-400 font-semibold">
          {state === "listening"
            ? "Listening..."
            : state === "thinking"
            ? "Thinking & Connecting Memory..."
            : "Speaking Aloud..."}
        </span>
      </div>
    </div>
  );
}
