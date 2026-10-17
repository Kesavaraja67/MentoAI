"use client";

import React from "react";

interface NumberPadProps {
  onSelectNumber: (num: number) => void;
  disabled?: boolean;
  maxNumber?: number;
}

export function NumberPad({
  onSelectNumber,
  disabled = false,
  maxNumber = 12,
}: NumberPadProps) {
  // Generate numbers from 0 to maxNumber (e.g. 0 to 12 or 20)
  const numbers = Array.from({ length: maxNumber + 1 }, (_, i) => i);

  return (
    <div className="w-full max-w-xl mx-auto">
      <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-7 gap-2.5 sm:gap-3 justify-center">
        {numbers.map((n) => (
          <button
            key={n}
            type="button"
            disabled={disabled}
            onClick={() => onSelectNumber(n)}
            className="min-w-[56px] min-h-[56px] flex items-center justify-center rounded-2xl bg-[#EAE6DC] hover:bg-[#D4CEBD] active:bg-[#7B9CB8] active:text-white text-[#1A1A2E] text-2xl font-bold font-child transition-all duration-150 shadow-xs active:scale-95 disabled:opacity-50 disabled:pointer-events-none cursor-pointer border border-[#CDD2DB]/60"
            aria-label={`Select number ${n}`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
