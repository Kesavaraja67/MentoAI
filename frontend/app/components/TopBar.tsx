"use client";

import React from "react";
import { Persona } from "../lib/api";
import { Trash, Handshake, Database, ArrowSquareOut } from "@phosphor-icons/react";

interface TopBarProps {
  personas: Persona[];
  currentPersonaId: string;
  onSelectPersona: (id: string) => void;
  graphModeEnabled: boolean;
  onToggleGraphMode: (enabled: boolean) => void;
  onOpenDigest: () => void;
  onForgetLearner: () => void;
}

export function TopBar({
  personas,
  currentPersonaId,
  onSelectPersona,
  graphModeEnabled,
  onToggleGraphMode,
  onOpenDigest,
  onForgetLearner,
}: TopBarProps) {
  return (
    <header className="w-full bg-[#090A0D] border-b border-white/[0.1] px-4 md:px-8 py-3 select-none relative z-30">
      <div className="max-w-[1680px] mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Heron AI Brand & Architectural System Spec */}
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 bg-[#FA3600] flex items-center justify-center font-mono font-bold text-black text-xs">
            M
          </div>
          <div className="flex items-center gap-2.5">
            <span className="font-display font-bold text-base tracking-tight text-white uppercase">
              MentoAI
            </span>
            <span className="heron-tag-brand">
              FALKOR-GRAPH // v2.0
            </span>
            <span className="hidden md:inline font-mono text-[10px] text-[#5C5C58]">
              ARCHITECTURAL COMPANION
            </span>
          </div>
        </div>

        {/* Center: Heron AI Persona Selector with Solid Grid Divisions */}
        <div className="flex items-center border border-white/[0.12] bg-[#0E0F14] text-xs">
          <span className="font-mono text-[10px] uppercase text-[#8C8C88] px-3 py-1.5 border-r border-white/[0.12] tracking-wider">
            Learner // Target
          </span>
          {personas.map((p, idx) => {
            const isSelected = p.id === currentPersonaId;
            return (
              <button
                key={p.id}
                onClick={() => onSelectPersona(p.id)}
                className={`px-3.5 py-1.5 font-mono text-xs uppercase tracking-wider transition-all duration-200 cursor-pointer ${
                  idx < personas.length - 1 ? "border-r border-white/[0.12]" : ""
                } ${
                  isSelected
                    ? "bg-[#FA3600] text-white font-bold"
                    : "text-[#8C8C88] hover:text-white hover:bg-white/[0.04]"
                }`}
              >
                {p.id === "mira" ? "Mira [7YO]" : p.id === "arjun" ? "Arjun [TEEN]" : "Lakshmi [ADULT]"}
              </button>
            );
          })}
        </div>

        {/* Right Telemetry Controls */}
        <div className="flex items-center gap-2">
          {/* Rule 3 Memory Toggle */}
          <button
            onClick={() => onToggleGraphMode(!graphModeEnabled)}
            className={`flex items-center gap-2 px-3 py-1.5 border font-mono text-[11px] uppercase tracking-wider transition-all cursor-pointer ${
              graphModeEnabled
                ? "border-[#FA3600] bg-[#FA3600]/10 text-[#FA3600] hover:bg-[#FA3600] hover:text-white"
                : "border-white/20 bg-transparent text-white/50 hover:text-white"
            }`}
            title="Toggle FalkorDB Graph Memory (Rule 3 Verification)"
          >
            <span className={`w-1.5 h-1.5 ${graphModeEnabled ? "bg-[#FA3600]" : "bg-white/40"}`} />
            <span>FALKOR: {graphModeEnabled ? "ACTIVE" : "OFFLINE"}</span>
          </button>

          {/* Grown-Up Digest Trigger */}
          <button
            onClick={onOpenDigest}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-white/[0.12] bg-[#0E0F14] hover:border-white/40 text-white font-mono text-[11px] uppercase tracking-wider transition-all cursor-pointer"
          >
            <Handshake size={14} weight="duotone" className="text-[#FA3600]" />
            <span>Digest</span>
          </button>

          {/* Privacy Forget Learner */}
          <button
            onClick={onForgetLearner}
            className="p-1.5 border border-white/[0.12] text-[#8C8C88] hover:text-rose-400 hover:border-rose-500/40 transition-colors cursor-pointer"
            title="Erase learner graph memory (Rule 6 Privacy)"
          >
            <Trash size={15} />
          </button>
        </div>
      </div>
    </header>
  );
}
