"use client";

import React, { useState, useEffect } from "react";
import { DecisionTrace, fetchDecisionTrace } from "../lib/api";
import { Eye, LinkSimple } from "@phosphor-icons/react";

interface WhyPanelProps {
  latestDecisionId?: string | null;
}

export function WhyPanel({ latestDecisionId }: WhyPanelProps) {
  const [trace, setTrace] = useState<DecisionTrace | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!latestDecisionId) return;
    setLoading(true);
    fetchDecisionTrace(latestDecisionId)
      .then((data) => setTrace(data))
      .catch((err) => console.error("Failed to load decision trace:", err))
      .finally(() => setLoading(false));
  }, [latestDecisionId]);

  return (
    <div className="heron-panel p-4 flex flex-col h-full relative overflow-hidden crosshair-tl crosshair-tr select-none">
      {/* Heron AI Architectural Header */}
      <div className="flex items-center justify-between pb-2.5 mb-2 heron-border-b-dashed text-[10px] font-mono text-[#8C8C88] relative z-10">
        <div className="flex items-center gap-2">
          <span className="text-[#FA3600] font-bold">+</span>
          <span className="uppercase tracking-wider font-semibold text-white">
            REASONING-TRACE // PROVENANCE
          </span>
        </div>
        <span className="heron-tag-brand">
          BECAUSE LOGIC
        </span>
      </div>

      {/* Body Content */}
      <div className="mt-2 flex-1 overflow-y-auto space-y-3.5 pr-1 font-mono">
        {loading ? (
          <div className="py-12 text-center text-[#8C8C88] text-xs flex flex-col items-center gap-2">
            <div className="w-4 h-4 border-2 border-[#FA3600] border-t-transparent rounded-full animate-spin" />
            <span>TRAVERSING FALKORDB PROVENANCE...</span>
          </div>
        ) : !trace || !trace.decision ? (
          <div className="py-12 text-center text-[#5C5C58] text-xs flex flex-col items-center gap-2">
            <Eye size={28} weight="thin" className="text-[#5C5C58]" />
            <span className="text-[#8C8C88]">AWAITING CONVERSATIONAL TURN</span>
            <span className="text-[10px] text-[#5C5C58] max-w-[280px]">
              Every pedagogical move is grounded in FalkorDB multi-hop edges with mathematical transparency.
            </span>
          </div>
        ) : (
          <>
            {/* Move Strategy Box */}
            <div className="p-3 bg-[#15161D] border border-white/[0.1] relative">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs uppercase font-bold text-[#FA3600] tracking-wider">
                  MOVE // {trace.decision.chosen_move}
                </span>
                <span className="text-[10px] text-white bg-black px-2 py-0.5 border border-white/10">
                  CONF {Math.round(trace.decision.confidence * 100)}%
                </span>
              </div>

              {/* Hatched Confidence Telemetry Bar */}
              <div className="w-full bg-[#0E0F14] h-2 mb-2 border border-white/[0.1] overflow-hidden">
                <div
                  className="bg-hatched h-full"
                  style={{ width: `${Math.round(trace.decision.confidence * 100)}%` }}
                />
              </div>

              <p className="text-xs text-[#EDEDED] font-sans leading-relaxed">
                {trace.decision.rationale}
              </p>
            </div>

            {/* Target Concept */}
            {trace.chosen_target && (
              <div className="p-2.5 bg-[#0E0F14] border border-white/[0.1] text-xs flex items-center justify-between">
                <span className="text-[#8C8C88] text-[10px]">TARGET CONCEPT:</span>
                <span className="text-[#FA3600] font-bold">
                  {trace.chosen_target}
                </span>
              </div>
            )}

            {/* BECAUSE Provenance Edges */}
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#8C8C88] mb-2 flex items-center gap-1.5">
                <span className="text-[#FA3600]">+</span>
                <span>BECAUSE Antecedents // Multi-Hop Trace</span>
              </div>

              <div className="space-y-1.5">
                {trace.because_items.length === 0 ? (
                  <p className="text-xs text-[#5C5C58] italic p-2 bg-[#0E0F14] border border-white/[0.05]">
                    No explicit prior antecedents linked.
                  </p>
                ) : (
                  trace.because_items.map((b, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-[#0E0F14] border border-white/[0.08] text-xs flex items-start gap-2 hover:border-[#FA3600]/40 transition-colors"
                    >
                      <LinkSimple size={14} weight="bold" className="text-[#FA3600] shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="heron-tag-brand text-[9px]">
                            {b.type}
                          </span>
                        </div>
                        <p className="text-[#EDEDED] text-[11px] font-sans leading-relaxed">
                          {b.note || b.text}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
