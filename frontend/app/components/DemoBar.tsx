"use client";

import React from "react";
import {
  GearSix,
  ArrowClockwise,
  ToggleLeft,
  ToggleRight,
  Sun,
  CheckCircle,
  CalendarCheck,
} from "@phosphor-icons/react";

interface DemoBarProps {
  dayLabel: string;
  graphMode: "on" | "off";
  onToggleGraphMode: () => void;
  onEndSession: () => void;
  onNextDay: () => void;
  onResetDemo: () => void;
  onOpenSettings: () => void;
  isSessionActive: boolean;
}

export function DemoBar({
  dayLabel,
  graphMode,
  onToggleGraphMode,
  onEndSession,
  onNextDay,
  onResetDemo,
  onOpenSettings,
  isSessionActive,
}: DemoBarProps) {
  return (
    <header className="w-full bg-[#1E2532] text-[#E0E4EC] px-4 py-2.5 border-b border-[#3A4154] flex flex-wrap items-center justify-between gap-3 text-xs font-mono shadow-md select-none">
      {/* Left: Product Brand & Day indicator */}
      <div className="flex items-center gap-3">
        <span className="font-bold tracking-wider text-sm text-white flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#F5C842]"></span>
          MENTOAI
        </span>
        <span className="text-[#3A4154]">|</span>
        <div className="flex items-center gap-1.5 bg-[#2B3446] px-2.5 py-1 rounded-md text-[#F5C842] font-semibold">
          <CalendarCheck size={14} weight="bold" />
          <span data-testid="day-label">{dayLabel}</span>
        </div>
      </div>

      {/* Center: Graph Mode Toggle (Ablation Switch) */}
      <div className="flex items-center gap-2 bg-[#2B3446] px-3 py-1 rounded-lg border border-[#3A4154]">
        <span className="text-[#A0AEC0] text-[11px] font-sans font-medium uppercase tracking-wider">
          Graph Intelligence:
        </span>
        <button
          data-testid="graph-mode-toggle"
          onClick={onToggleGraphMode}
          className={`flex items-center gap-1.5 font-bold px-2 py-0.5 rounded transition-colors ${
            graphMode === "on"
              ? "text-[#F5C842] hover:bg-[#3A4154]"
              : "text-[#E53E3E] hover:bg-[#3A4154]"
          }`}
          title="Toggle FalkorDB Graph Memory On/Off (Rule 3 Ablation)"
        >
          {graphMode === "on" ? (
            <>
              <ToggleRight size={20} weight="fill" className="text-[#F5C842]" />
              <span>ON</span>
            </>
          ) : (
            <>
              <ToggleLeft size={20} weight="fill" className="text-[#A0AEC0]" />
              <span>OFF (Ablation)</span>
            </>
          )}
        </button>
      </div>

      {/* Right: Demo Actions */}
      <div className="flex items-center gap-2">
        {isSessionActive ? (
          <button
            data-testid="end-session-btn"
            onClick={onEndSession}
            className="flex items-center gap-1.5 bg-[#D97B22] hover:bg-[#C06A1A] text-white px-3 py-1 rounded-md font-semibold transition-colors shadow-xs"
          >
            <CheckCircle size={15} weight="bold" />
            <span>End Session</span>
          </button>
        ) : (
          <button
            data-testid="next-day-btn"
            onClick={onNextDay}
            className="flex items-center gap-1.5 bg-[#2E7D32] hover:bg-[#256629] text-white px-3 py-1 rounded-md font-semibold transition-colors shadow-xs"
          >
            <Sun size={15} weight="bold" />
            <span>Next Day</span>
          </button>
        )}

        <button
          data-testid="reset-demo-btn"
          onClick={onResetDemo}
          className="flex items-center gap-1 bg-[#2B3446] hover:bg-[#3A4154] text-[#E0E4EC] px-2.5 py-1 rounded-md transition-colors"
          title="Reset all personas and sessions back to initial state"
        >
          <ArrowClockwise size={14} weight="bold" />
          <span>Reset</span>
        </button>

        <button
          onClick={onOpenSettings}
          className="flex items-center justify-center p-1.5 rounded-md bg-[#2B3446] hover:bg-[#3A4154] text-[#E0E4EC] transition-colors"
          title="BYOK LLM Settings"
          aria-label="Open settings"
        >
          <GearSix size={16} weight="bold" />
        </button>
      </div>
    </header>
  );
}
