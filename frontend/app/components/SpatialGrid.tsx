"use client";

import React, { useEffect, useRef } from "react";

interface SpatialGridProps {
  state: "listening" | "thinking" | "speaking";
}

export function SpatialGrid({ state }: SpatialGridProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    let mouse = {
      x: width * 0.5,
      y: height * 0.5,
      targetX: width * 0.5,
      targetY: height * 0.5,
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    let time = 0;

    // 3D Perspective Grid Parameters
    const cols = 28;
    const rows = 20;
    const fov = 400;

    const render = () => {
      time += prefersReducedMotion ? 0.003 : state === "thinking" ? 0.025 : state === "speaking" ? 0.02 : 0.01;

      // Mouse damping
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      ctx.fillStyle = "#090A0D";
      ctx.fillRect(0, 0, width, height);

      ctx.lineWidth = 1;

      const centerX = width * 0.5;
      const centerY = height * 0.65;
      const cameraPitch = (mouse.y / height - 0.5) * 0.2;
      const cameraYaw = (mouse.x / width - 0.5) * 0.2;

      const gridPoints: { x: number; y: number; z: number; visible: boolean }[][] = [];

      for (let r = 0; r < rows; r++) {
        gridPoints[r] = [];
        const z = 80 + r * 38;
        const scale = fov / (fov + z);

        for (let c = 0; c < cols; c++) {
          const worldX = (c - cols / 2) * 65;
          const worldZ = z;

          // Wave displacement function
          const normDist = Math.sqrt(worldX * worldX + worldZ * worldZ) * 0.005;
          let waveY = Math.sin(normDist * 5 - time * 2) * 12;

          if (state === "speaking") {
            waveY += Math.sin(c * 0.8 + time * 4) * 16 * Math.cos(r * 0.5);
          } else if (state === "thinking") {
            waveY += Math.cos(c * 0.5 - time * 3) * 14 * Math.sin(r * 0.6 + time);
          }

          // Camera rotation
          const rotX = worldX * Math.cos(cameraYaw) - (worldZ - 300) * Math.sin(cameraYaw);
          const rotZ = worldX * Math.sin(cameraYaw) + (worldZ - 300) * Math.cos(cameraYaw) + 300;
          const rotY = waveY + (rotZ - 300) * Math.sin(cameraPitch);

          const projScale = fov / (fov + rotZ);
          const screenX = centerX + rotX * projScale;
          const screenY = centerY + rotY * projScale;

          gridPoints[r][c] = {
            x: screenX,
            y: screenY,
            z: rotZ,
            visible: projScale > 0 && screenX > -50 && screenX < width + 50 && screenY < height + 50,
          };
        }
      }

      // Draw Perspective Grid Lines
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const p = gridPoints[r][c];
          if (!p.visible) continue;

          // Horizontal wireframe lines
          if (c < cols - 1) {
            const nextP = gridPoints[r][c + 1];
            if (nextP.visible) {
              const alpha = Math.max(0.02, (1 - r / rows) * 0.14);
              ctx.strokeStyle =
                state === "speaking"
                  ? `rgba(250, 54, 0, ${alpha * 1.5})`
                  : `rgba(255, 255, 255, ${alpha})`;
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(nextP.x, nextP.y);
              ctx.stroke();
            }
          }

          // Depth wireframe lines
          if (r < rows - 1) {
            const depthP = gridPoints[r + 1][c];
            if (depthP.visible) {
              const alpha = Math.max(0.02, (1 - r / rows) * 0.12);
              ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
              ctx.beginPath();
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(depthP.x, depthP.y);
              ctx.stroke();
            }
          }

          // Heron AI Architectural Intersection Crosshairs
          if (r % 3 === 0 && c % 4 === 0) {
            const pointAlpha = Math.max(0.04, (1 - r / rows) * 0.35);
            ctx.fillStyle =
              r === 3 && c === 12 && state === "thinking"
                ? "rgba(250, 54, 0, 0.8)"
                : `rgba(255, 255, 255, ${pointAlpha})`;
            ctx.fillRect(p.x - 1, p.y - 1, 2.5, 2.5);
          }
        }
      }

      // Architectural Top Horizon
      ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, height * 0.1);
      ctx.lineTo(width, height * 0.1);
      ctx.stroke();
      ctx.setLineDash([]);

      if (!prefersReducedMotion) {
        animId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      if (animId) cancelAnimationFrame(animId);
    };
  }, [state]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 select-none"
    />
  );
}
