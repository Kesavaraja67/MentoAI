"use client";

import React, { useEffect, useRef } from "react";
import { Microphone, MicrophoneSlash, Sparkle, Stop, Waveform } from "@phosphor-icons/react";

interface VoiceCoreProps {
  state: "listening" | "thinking" | "speaking";
  isMuted: boolean;
  onToggleMute: () => void;
  onClickOrb?: () => void;
  onBargeIn?: () => void;
}

export function VoiceCore({
  state,
  isMuted,
  onToggleMute,
  onClickOrb,
  onBargeIn,
}: VoiceCoreProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let animId: number;
    const size = 300;
    canvas.width = size * window.devicePixelRatio;
    canvas.height = size * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const center = size / 2;
    let time = 0;

    // 3D Wireframe Icosahedron / Gyro Ring Coordinates
    const ringRadii = [60, 78, 96, 114];

    const render = () => {
      time += prefersReducedMotion ? 0.005 : state === "thinking" ? 0.04 : state === "speaking" ? 0.03 : 0.015;

      ctx.clearRect(0, 0, size, size);

      // Outer Architectural Compass Ticks (Heron CAD Aesthetic)
      ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
      ctx.lineWidth = 1;
      const tickCount = 36;
      for (let i = 0; i < tickCount; i++) {
        const angle = (i / tickCount) * Math.PI * 2;
        const isMajor = i % 9 === 0;
        const innerR = isMajor ? 132 : 138;
        const outerR = 144;

        ctx.beginPath();
        ctx.moveTo(center + Math.cos(angle) * innerR, center + Math.sin(angle) * innerR);
        ctx.lineTo(center + Math.cos(angle) * outerR, center + Math.sin(angle) * outerR);
        ctx.stroke();
      }

      // Outer Dashed Drafting Ring
      ctx.strokeStyle = "rgba(255, 255, 255, 0.14)";
      ctx.setLineDash([3, 5]);
      ctx.beginPath();
      ctx.arc(center, center, 128, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Rotating 3D Concentric Wireframe Gyro Rings
      ringRadii.forEach((r, idx) => {
        const tilt = (idx * Math.PI) / 3 + time * (idx % 2 === 0 ? 0.8 : -0.8);
        const pitch = Math.sin(time * 0.5 + idx) * 0.4;

        ctx.save();
        ctx.translate(center, center);
        ctx.rotate(tilt);

        ctx.beginPath();
        const segments = 48;
        for (let s = 0; s <= segments; s++) {
          const theta = (s / segments) * Math.PI * 2;
          let wave = 0;
          if (state === "speaking") {
            wave = Math.sin(theta * 6 + time * 4) * (idx === 1 ? 7 : 4);
          } else if (state === "thinking") {
            wave = Math.cos(theta * 4 - time * 3) * 5;
          }

          const currentR = r + wave;
          const x = currentR * Math.cos(theta);
          const y = currentR * Math.sin(theta) * Math.cos(pitch);

          if (s === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.closePath();

        if (state === "speaking") {
          ctx.strokeStyle = idx === 1 ? "#FA3600" : "rgba(250, 54, 0, 0.45)";
          ctx.lineWidth = idx === 1 ? 1.5 : 1;
        } else if (state === "thinking") {
          ctx.strokeStyle = idx === 2 ? "#FA3600" : "rgba(255, 255, 255, 0.35)";
          ctx.lineWidth = 1;
        } else {
          ctx.strokeStyle = idx === 0 ? "rgba(250, 54, 0, 0.6)" : "rgba(255, 255, 255, 0.2)";
          ctx.lineWidth = 1;
        }

        ctx.stroke();
        ctx.restore();
      });

      // Central Heron Vermilion Core Beacon
      const coreR = 40;
      ctx.save();
      ctx.beginPath();
      ctx.arc(center, center, coreR, 0, Math.PI * 2);
      ctx.fillStyle = "#0F1015";
      ctx.fill();

      // Border with Heron Vermilion `#FA3600`
      ctx.strokeStyle =
        state === "speaking" || state === "thinking"
          ? "#FA3600"
          : "rgba(255, 255, 255, 0.25)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Central crosshair lines
      ctx.strokeStyle = "rgba(250, 54, 0, 0.5)";
      ctx.beginPath();
      ctx.moveTo(center - 12, center);
      ctx.lineTo(center + 12, center);
      ctx.moveTo(center, center - 12);
      ctx.lineTo(center, center + 12);
      ctx.stroke();

      ctx.restore();

      if (!prefersReducedMotion) {
        animId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  }, [state]);

  return (
    <div className="relative flex flex-col items-center justify-center p-3 select-none">
      {/* Heron AI Architectural Telemetry Header */}
      <div className="w-full flex items-center justify-between pb-2 mb-1 heron-border-b-dashed text-[10px] font-mono text-[#8C8C88]">
        <div className="flex items-center gap-1.5">
          <span className="text-[#FA3600] font-bold">+</span>
          <span>VOICE-CORE // 3D-OSCILLATOR</span>
        </div>
        <div className="flex items-center gap-2">
          <span>FREQ: 48.0kHz</span>
          <span className="text-white/20">|</span>
          <span className="text-[#FA3600] font-bold">{state.toUpperCase()}</span>
        </div>
      </div>

      {/* 3D Wireframe Gyro Organism */}
      <div
        onClick={onClickOrb || onToggleMute}
        className="relative w-60 h-60 md:w-68 md:h-68 flex items-center justify-center cursor-pointer group"
        title={isMuted ? "Unmute microphone" : "Click to speak / interact"}
      >
        <canvas ref={canvasRef} className="w-full h-full pointer-events-none" />

        {/* Center Technical Glyph */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          {isMuted ? (
            <MicrophoneSlash size={24} weight="bold" className="text-rose-400" />
          ) : state === "thinking" ? (
            <Sparkle size={24} weight="fill" className="text-[#FA3600] animate-spin" />
          ) : state === "speaking" ? (
            <Waveform size={24} weight="bold" className="text-[#FA3600] animate-pulse" />
          ) : (
            <Microphone
              size={24}
              weight="bold"
              className="text-[#FA3600] animate-pulse"
            />
          )}
          <span className="mt-2 text-[9px] font-mono tracking-wider uppercase text-white/50 group-hover:text-[#FA3600] transition-colors">
            {isMuted ? "Click to talk" : "Mic listening"}
          </span>
        </div>
      </div>

      {/* Telemetry Status Bar & Heron Vermilion Controls */}
      <div className="w-full mt-1.5 pt-2 heron-border-t-dashed flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-[#FA3600]" />
          <span className="font-mono text-xs uppercase tracking-wider text-white font-semibold">
            {state === "listening"
              ? "ATTENTIVE [LISTENING]"
              : state === "thinking"
              ? "SYNTHESIZING [TRAVERSAL]"
              : "VOCALIZING [STREAMING]"}
          </span>
        </div>

        {/* Barge-In / Interrupt Button (Heron vermilion mechanical button) */}
        {state === "speaking" && onBargeIn && (
          <button
            onClick={onBargeIn}
            className="heron-btn-brand px-3 py-1 text-[11px] flex items-center gap-1.5 cursor-pointer"
            title="Interrupt voice"
          >
            <Stop size={12} weight="fill" />
            <span>INTERRUPT // STOP</span>
          </button>
        )}
      </div>
    </div>
  );
}
