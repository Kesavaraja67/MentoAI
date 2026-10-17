"use client";

import React from "react";
import { X, Books } from "@phosphor-icons/react";

interface VisualCard {
  id: string;
  kind: string;
  payload: any;
}

interface VisualStageProps {
  card: VisualCard | null;
  onDismiss: () => void;
}

export function VisualStage({ card, onDismiss }: VisualStageProps) {
  if (!card) return null;

  return (
    <div className="heron-panel p-4 relative crosshair-tl crosshair-tr border-[#FA3600]/40 animate-in fade-in zoom-in-95 duration-200">
      <button
        onClick={onDismiss}
        className="absolute top-3 right-3 text-[#8C8C88] hover:text-white p-1 border border-white/10 hover:border-white/30 transition-colors cursor-pointer"
        title="Dismiss artifact"
      >
        <X size={13} />
      </button>

      <div className="flex items-center gap-2 mb-2.5 pb-1.5 heron-border-b-dashed">
        <Books size={16} weight="duotone" className="text-[#FA3600]" />
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
          {card.payload.title || "VISUAL ARTIFACT // STAGE"}
        </h4>
      </div>

      {card.kind === "story_card" && (
        <div className="bg-[#0E0F14] p-3 border border-white/[0.08] flex flex-col gap-2">
          <p className="text-xs text-[#EDEDED] leading-relaxed font-sans italic">
            "{card.payload.caption}"
          </p>
          {card.payload.tags && (
            <div className="flex flex-wrap gap-1 mt-1 font-mono">
              {card.payload.tags.map((tag: string, i: number) => (
                <span key={i} className="heron-tag-brand text-[9px]">
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {card.kind === "svg" && card.payload.svg && (
        <div
          className="bg-[#0E0F14] p-3 flex items-center justify-center border border-white/[0.08]"
          dangerouslySetInnerHTML={{ __html: card.payload.svg }}
        />
      )}
    </div>
  );
}
