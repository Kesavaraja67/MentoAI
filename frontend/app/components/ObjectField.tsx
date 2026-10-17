"use client";

import React from "react";
import Image from "next/image";

interface ObjectFieldProps {
  objectSet: string;
  a: number;
  b: number;
  op: "+" | "-" | "?" | "count";
  easier?: boolean;
}

export function ObjectField({ objectSet, a, b, op }: ObjectFieldProps) {
  // Map objectSet to appropriate SVG file
  let assetName = "rocket.svg";
  if (objectSet === "dinosaur") {
    assetName = "egg.svg";
  } else if (objectSet === "cricket") {
    assetName = "ball.svg";
  } else {
    // Default space
    assetName = "fuel_cell.svg";
  }

  const assetPath = `/objects/${assetName}`;

  // Safe clamping for rendering (max 20 objects total)
  const countA = Math.max(0, Math.min(a, 20));
  const countB = op === "+" || op === "?" ? Math.max(0, Math.min(b, 20)) : 0;

  return (
    <div className="w-full flex flex-col items-center justify-center p-6 bg-[#FFFFFF] rounded-2xl border-2 border-[#CDD2DB] shadow-xs select-none">
      <div className="w-full flex flex-wrap items-center justify-center gap-6 md:gap-10">
        {/* First group (countA) */}
        <div className="flex flex-col items-center gap-2">
          <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-[280px]">
            {Array.from({ length: countA }).map((_, i) => (
              <div
                key={`a-${i}`}
                className="w-12 h-12 md:w-14 md:h-14 flex items-center justify-center bg-[#F7F4ED] rounded-xl border border-[#7B9CB8]/40 shadow-xs transition-transform hover:scale-105"
              >
                <Image
                  src={assetPath}
                  alt={`${objectSet} object ${i + 1}`}
                  width={40}
                  height={40}
                  className="w-8 h-8 md:w-10 md:h-10 object-contain pointer-events-none"
                />
              </div>
            ))}
          </div>
          <span className="text-xs font-mono font-bold text-[#4A4A6A]">
            {countA}
          </span>
        </div>

        {/* Operator separator */}
        {countB > 0 && (
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-[#EAE6DC] text-2xl font-bold text-[#1A1A2E] shadow-inner">
            {op === "?" ? "+" : op}
          </div>
        )}

        {/* Second group (countB) if addition or missing addend */}
        {countB > 0 && (
          <div className="flex flex-col items-center gap-2">
            <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-[280px]">
              {Array.from({ length: countB }).map((_, i) => (
                <div
                  key={`b-${i}`}
                  className="w-12 h-12 md:w-14 md:h-14 flex items-center justify-center bg-[#F7F4ED] rounded-xl border border-[#7B9CB8]/40 shadow-xs transition-transform hover:scale-105"
                >
                  <Image
                    src={assetPath}
                    alt={`${objectSet} object b-${i + 1}`}
                    width={40}
                    height={40}
                    className="w-8 h-8 md:w-10 md:h-10 object-contain pointer-events-none"
                  />
                </div>
              ))}
            </div>
            <span className="text-xs font-mono font-bold text-[#4A4A6A]">
              {countB}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
