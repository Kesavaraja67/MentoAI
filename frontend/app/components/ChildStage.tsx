"use client";

import React, { useState } from "react";
import { Sparkle, Check, ArrowRight } from "@phosphor-icons/react";
import { Problem } from "../lib/api";
import { ObjectField } from "./ObjectField";
import { NumberPad } from "./NumberPad";

interface ChildStageProps {
  childName: string;
  problem: Problem;
  story: string;
  tutorText: string;
  isCorrect: boolean | null;
  turnCount: number;
  onAnswer: (given: number, freeText?: string) => void;
  isSubmitting: boolean;
}

export function ChildStage({
  childName,
  problem,
  story,
  tutorText,
  isCorrect,
  turnCount,
  onAnswer,
  isSubmitting,
}: ChildStageProps) {
  const [reflectiveText, setReflectiveText] = useState("");
  const [showReflection, setShowReflection] = useState(false);

  // Derive problem question text
  let questionText = `${problem.a} + ${problem.b} = ?`;
  if (problem.op === "-") {
    questionText = `${problem.a} - ${problem.b} = ?`;
  } else if (problem.op === "?") {
    questionText = `${problem.a} + ? = ${problem.b}`;
  } else if (problem.op === "count") {
    questionText = "How many in all?";
  }

  const handleNumberSelect = (num: number) => {
    if (isSubmitting) return;
    onAnswer(num);
  };

  const handleContinue = () => {
    setShowReflection(false);
    setReflectiveText("");
  };

  return (
    <div className="flex-1 flex flex-col justify-between p-6 sm:p-8 md:p-10 bg-[#F7F4ED] min-h-[calc(100vh-48px)] text-[#1A1A2E] overflow-y-auto">
      {/* Top Header: Quiet Progress */}
      <div className="w-full flex items-center justify-between pb-4 border-b border-[#7B9CB8]/30 text-xs font-mono font-medium text-[#4A4A6A]">
        <span>LEARNER: {childName.toUpperCase()}</span>
        <span>PROBLEM {turnCount}</span>
      </div>

      {/* Main Content Center */}
      <div className="w-full max-w-2xl mx-auto flex flex-col items-center gap-6 my-auto py-4">
        {/* Story Frame */}
        {story && (
          <p className="text-center text-lg md:text-xl font-semibold text-[#4A4A6A] leading-relaxed max-w-xl">
            {story}
          </p>
        )}

        {/* Problem Equation / Prompt */}
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-wide text-center text-[#1A1A2E]">
          {questionText}
        </h1>

        {/* Object Field Illustration Area */}
        <ObjectField
          objectSet={problem.story_slots.object_set || "space"}
          a={problem.a}
          b={problem.b}
          op={problem.op}
          easier={problem.story_slots.easier}
        />

        {/* Tutor Bubble (Always warm amber, never red or harsh) */}
        {tutorText && (
          <div className="w-full bg-[#F5C842] rounded-2xl p-4 sm:p-5 shadow-xs border-2 border-[#1A1A2E]/10 flex items-start gap-3 transition-all duration-300">
            <div className="p-2 rounded-xl bg-[#1A1A2E] text-[#F5C842] shrink-0 mt-0.5">
              <Sparkle size={20} weight="fill" />
            </div>
            <div className="flex-1">
              <span className="block text-[11px] font-mono font-bold uppercase tracking-wider text-[#1A1A2E]/70 mb-0.5">
                Tutor
              </span>
              <p className="text-base sm:text-lg font-bold text-[#1A1A2E] leading-snug">
                {tutorText}
              </p>
            </div>
          </div>
        )}

        {/* Optional Reflective Prompt (after correct answer) */}
        {isCorrect && (
          <div className="w-full bg-[#FFFFFF] rounded-2xl p-5 border-2 border-[#4C9A6A] flex flex-col gap-3 shadow-xs">
            <div className="flex items-center gap-2 text-[#4C9A6A] font-bold text-sm">
              <Check size={18} weight="bold" />
              <span>Great thinking! How did you get it?</span>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={reflectiveText}
                onChange={(e) => setReflectiveText(e.target.value)}
                placeholder="I counted on my fingers, I remembered..."
                className="flex-1 bg-[#F7F4ED] rounded-xl px-4 py-2.5 text-sm font-child border border-[#CDD2DB] outline-none focus:border-[#7B9CB8]"
              />
              <button
                onClick={handleContinue}
                className="flex items-center gap-1.5 px-4 py-2.5 bg-[#4C9A6A] hover:bg-[#3d7f56] text-white rounded-xl text-sm font-bold shadow-xs cursor-pointer"
              >
                <span>Continue</span>
                <ArrowRight size={16} weight="bold" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Number Pad */}
      <div className="w-full pt-4 border-t border-[#7B9CB8]/20 flex flex-col items-center">
        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#4A4A6A] mb-3">
          Tap your answer:
        </span>
        <NumberPad
          onSelectNumber={handleNumberSelect}
          disabled={isSubmitting}
          maxNumber={Math.max(12, problem.answer + 5)}
        />
      </div>
    </div>
  );
}
