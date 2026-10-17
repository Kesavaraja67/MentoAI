"use client";

import React, { useEffect, useRef } from "react";
import { Waveform, ChatTeardropDots } from "@phosphor-icons/react";

interface LiveSubtitlesProps {
  personText: string;
  isPersonFinal: boolean;
  mentoaiText: string;
  state: "listening" | "thinking" | "speaking";
}

export function LiveSubtitles({
  personText,
  isPersonFinal,
  mentoaiText,
  state,
}: LiveSubtitlesProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [personText, mentoaiText]);

  return (
    <div
      ref={containerRef}
      className="heron-panel p-4 min-h-[160px] max-h-[200px] overflow-y-auto flex flex-col justify-end gap-3 relative crosshair-tl crosshair-tr select-none"
    >
      {/* Heron AI Architectural Stream Header */}
      <div className="absolute top-2.5 left-4 right-4 flex items-center justify-between font-mono text-[10px] text-[#8C8C88] uppercase tracking-wider pb-1.5 heron-border-b-dashed pointer-events-none">
        <div className="flex items-center gap-1.5">
          <Waveform size={12} weight="bold" className="text-[#FA3600]" />
          <span>AUDIO-STREAM // SUBTITLES</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-[#FA3600] animate-pulse" />
          <span>LIVE-SYNC</span>
        </div>
      </div>

      {/* Person Subtitle */}
      {personText && (
        <div className="mt-5 text-sm transition-all font-mono">
          <div className="text-[10px] text-[#FA3600] uppercase tracking-wider font-semibold mb-0.5">
            [01 // LEARNER]
          </div>
          <p
            className={`text-sm leading-relaxed font-sans ${
              isPersonFinal ? "text-[#EDEDED]" : "italic text-[#8C8C88]"
            }`}
          >
            {personText}
          </p>
        </div>
      )}

      {/* MentoAI Subtitle */}
      {mentoaiText && (
        <div className="mt-2 text-sm transition-all font-mono">
          <div className="text-[10px] text-[#FA3600] uppercase tracking-wider font-semibold mb-0.5 flex items-center gap-2">
            <span>[02 // MENTO-CORE]</span>
            {state === "speaking" && (
              <span className="text-[9px] px-1 py-0.2 bg-[#FA3600]/20 text-[#FA3600] border border-[#FA3600]/40">
                SYNTHESIZING
              </span>
            )}
          </div>
          <p className="text-base text-white font-medium leading-relaxed font-sans">
            {mentoaiText}
          </p>
        </div>
      )}

      {/* Empty State / Invitation */}
      {!personText && !mentoaiText && (
        <div className="text-center py-5 text-[#8C8C88] text-xs flex flex-col items-center justify-center gap-1">
          <ChatTeardropDots size={22} weight="thin" className="text-[#5C5C58]" />
          <p className="font-mono text-white text-xs">
            SPEAK ALOUD OR TYPE BELOW
          </p>
          <p className="text-[10px] text-[#5C5C58] font-mono">
            MentoAI connects each spoken thought to persistent graph memory.
          </p>
        </div>
      )}
    </div>
  );
}
