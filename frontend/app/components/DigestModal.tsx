"use client";

import React from "react";
import { DigestItem } from "../lib/api";
import { X, Handshake, CheckCircle, WarningCircle, Compass } from "@phosphor-icons/react";

interface DigestModalProps {
  isOpen: boolean;
  onClose: () => void;
  digests: DigestItem[];
}

export function DigestModal({ isOpen, onClose, digests }: DigestModalProps) {
  if (!isOpen) return null;

  const latest = digests[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="heron-panel w-full max-w-2xl p-6 text-[#EDEDED] max-h-[85vh] overflow-y-auto relative crosshair-tl crosshair-tr border-white/20">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-[#8C8C88] hover:text-white p-1 border border-white/10 hover:border-white/30 transition-colors cursor-pointer font-mono text-xs"
        >
          <X size={16} />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 pb-3 border-b border-white/[0.1]">
          <div className="w-8 h-8 bg-[#FA3600] flex items-center justify-center font-mono font-bold text-black text-sm">
            D
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-mono uppercase tracking-wide">
              Grown-Up Learning Digest // Telemetry
            </h2>
            <p className="text-[10px] font-mono text-[#8C8C88]">
              Traceable developmental summary extracted from FalkorDB graph memory
            </p>
          </div>
        </div>

        {!latest ? (
          <div className="py-12 text-center text-[#8C8C88] text-xs font-mono flex flex-col items-center gap-2">
            <Compass size={32} weight="thin" className="text-[#5C5C58]" />
            <span>NO SESSION REFLECTIONS LOGGED YET</span>
            <span className="text-[10px] text-[#5C5C58]">
              Complete a conversational turn to generate an automated developmental synthesis.
            </span>
          </div>
        ) : (
          <div className="mt-4 space-y-4 font-mono">
            {/* Note for Grownup */}
            {latest.text && (
              <div className="p-3.5 bg-[#15161D] border border-white/[0.1] text-xs text-[#EDEDED] leading-relaxed font-sans italic">
                "{latest.text}"
              </div>
            )}

            {/* Strengths & Breakthroughs */}
            {latest.strengths && latest.strengths.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-[#FA3600] mb-2 flex items-center gap-1.5 font-bold">
                  <CheckCircle size={13} weight="fill" />
                  DEMONSTRATED STRENGTHS // MASTERY
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {latest.strengths.map((s, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2.5 py-1 bg-[#0E0F14] text-white border border-white/20"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Shaky / Developing Areas */}
            {latest.shaky_areas && latest.shaky_areas.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-amber-400 mb-2 flex items-center gap-1.5 font-bold">
                  <WarningCircle size={13} weight="fill" />
                  CONCEPTS IN FORMATION // DEVELOPMENTAL
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {latest.shaky_areas.map((s, idx) => (
                    <span
                      key={idx}
                      className="text-xs px-2.5 py-1 bg-[#0E0F14] text-amber-300 border border-amber-500/30"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Suggested Offline Activities */}
            {latest.offline_activities && latest.offline_activities.length > 0 && (
              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-white mb-2 flex items-center gap-1.5 font-bold">
                  <Compass size={13} weight="duotone" className="text-[#FA3600]" />
                  RECOMMENDED OFFLINE EXPLORATIONS
                </h4>
                <ul className="space-y-1.5 text-xs text-[#8C8C88]">
                  {latest.offline_activities.map((act, idx) => (
                    <li
                      key={idx}
                      className="flex items-center gap-2 p-2 bg-[#0E0F14] border border-white/[0.06]"
                    >
                      <span className="w-1.5 h-1.5 bg-[#FA3600] shrink-0" />
                      <span className="font-sans text-[#EDEDED]">{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
