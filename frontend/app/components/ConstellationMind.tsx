"use client";

import React, { useState, useMemo } from "react";
import { MindGraph, MindNode } from "../lib/api";
import { Compass } from "@phosphor-icons/react";

interface ConstellationMindProps {
  mindData: MindGraph | null;
  activePulsingKey?: string | null;
  onSelectNode?: (node: MindNode) => void;
}

export function ConstellationMind({
  mindData,
  activePulsingKey,
  onSelectNode,
}: ConstellationMindProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<MindNode | null>(null);

  const nodes = mindData?.nodes || [];
  const edges = mindData?.edges || [];

  // Helper to reliably get a node's identifier (supports id or key)
  const getNodeId = (n: any, idx: number): string => {
    return n.id || n.key || `node_${idx}`;
  };

  // Compute 2D coordinates arranged with clear, non-overlapping spatial distribution
  const layout = useMemo(() => {
    if (!nodes.length) return {};
    const coords: Record<string, { x: number; y: number }> = {};
    const center = { x: 260, y: 185 };

    if (nodes.length === 1) {
      const id = getNodeId(nodes[0], 0);
      coords[id] = { x: center.x, y: center.y };
      return coords;
    }

    // Spread nodes evenly around an elliptical orbital ring
    nodes.forEach((n, idx) => {
      const id = getNodeId(n, idx);
      const angle = (idx / nodes.length) * 2 * Math.PI - Math.PI / 2;
      const radiusX = 135 + (idx % 2 === 0 ? 25 : -25);
      const radiusY = 95 + (idx % 2 === 0 ? 15 : -15);

      coords[id] = {
        x: Math.round(center.x + radiusX * Math.cos(angle)),
        y: Math.round(center.y + radiusY * Math.sin(angle)),
      };
    });
    return coords;
  }, [nodes]);

  const selectedNode = useMemo(() => {
    if (!selectedId) return null;
    return nodes.find((n, idx) => getNodeId(n, idx) === selectedId) || null;
  }, [selectedId, nodes]);

  const handleNodeClick = (node: MindNode, id: string) => {
    setSelectedId(id);
    if (onSelectNode) onSelectNode(node);
  };

  return (
    <div className="heron-panel p-4 flex flex-col h-full relative overflow-hidden crosshair-tl crosshair-tr select-none">
      {/* Heron AI Architectural Header */}
      <div className="flex items-center justify-between pb-2.5 mb-2 heron-border-b-dashed text-[10px] font-mono text-[#8C8C88] relative z-10">
        <div className="flex items-center gap-2">
          <span className="text-[#FA3600] font-bold">+</span>
          <span className="uppercase tracking-wider font-semibold text-white">
            CONSTELLATION-MIND // TOPOLOGICAL-GRAPH
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="heron-tag-brand">
            {nodes.length} NODES // {edges.length} EDGES
          </span>
        </div>
      </div>

      {/* Blueprint SVG Canvas */}
      <div className="relative flex-1 min-h-[340px] flex items-center justify-center overflow-hidden">
        {/* Subtle Background Coordinate Crosshairs */}
        <div className="absolute top-2 left-2 text-[9px] font-mono text-[#5C5C58]">
          + CAD-PLANE // J2000
        </div>
        <div className="absolute bottom-2 right-2 text-[9px] font-mono text-[#5C5C58]">
          FALKOR-DB PROVENANCE +
        </div>

        {nodes.length === 0 ? (
          <div className="text-center text-[#5C5C58] text-xs flex flex-col items-center gap-2 z-10">
            <Compass size={32} weight="thin" className="text-[#5C5C58] animate-spin-slow" />
            <span className="font-mono">NO CONCEPTS ACTIVE IN GRAPH</span>
            <span className="text-[10px] text-[#5C5C58]">
              Dialogue utterances automatically materialize concept nodes in FalkorDB.
            </span>
          </div>
        ) : (
          <svg
            className="w-full h-full min-h-[340px] select-none"
            viewBox="0 0 520 370"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Architectural Radial Grid Guides */}
            <circle
              cx="260"
              cy="185"
              r="60"
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeDasharray="2 4"
            />
            <circle
              cx="260"
              cy="185"
              r="120"
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeDasharray="3 4"
            />
            <circle
              cx="260"
              cy="185"
              r="170"
              fill="none"
              stroke="rgba(255,255,255,0.03)"
              strokeDasharray="4 4"
            />

            {/* Connecting Synaptic Edges */}
            {edges.map((e, idx) => {
              const src = layout[e.source];
              const tgt = layout[e.target];
              if (!src || !tgt) return null;

              const isPrereq = e.type === "PREREQUISITE_OF";
              return (
                <line
                  key={`edge_${e.source}_${e.target}_${idx}`}
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={isPrereq ? "#FA3600" : "rgba(255,255,255,0.22)"}
                  strokeWidth={isPrereq ? 1.5 : 1}
                  strokeDasharray={isPrereq ? undefined : "3 3"}
                  strokeOpacity={0.8}
                />
              );
            })}

            {/* Concept Nodes */}
            {nodes.map((n, idx) => {
              const id = getNodeId(n, idx);
              const pos = layout[id];
              if (!pos) return null;

              const isPulsing = activePulsingKey === id || activePulsingKey === n.name;
              const isSelected = selectedId === id;
              const isHovered = hoveredNode && getNodeId(hoveredNode, -1) === id;

              return (
                <g
                  key={id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  className="cursor-pointer"
                  onClick={() => handleNodeClick(n, id)}
                  onMouseEnter={() => setHoveredNode(n)}
                  onMouseLeave={() => setHoveredNode(null)}
                >
                  {/* Outer Non-jittering Architectural Frame (pointerEvents none prevents flicker) */}
                  {(isPulsing || isSelected || isHovered) && (
                    <rect
                      x="-14"
                      y="-14"
                      width="28"
                      height="28"
                      fill="none"
                      stroke="#FA3600"
                      strokeWidth="1.2"
                      strokeDasharray="3 2"
                      pointerEvents="none"
                      className="transition-all"
                    />
                  )}

                  {/* Core Square Geometric Mark */}
                  <rect
                    x="-7"
                    y="-7"
                    width="14"
                    height="14"
                    fill={isSelected || isPulsing ? "#FA3600" : isHovered ? "#FFFFFF" : "#0E0F14"}
                    stroke={isSelected || isPulsing ? "#FA3600" : "#FFFFFF"}
                    strokeWidth="1.5"
                    className="transition-colors duration-150"
                  />

                  {/* Node Label in Crisp Monospace with pointerEvents none */}
                  <text
                    y={20}
                    textAnchor="middle"
                    fill={isSelected || isHovered ? "#FA3600" : "#EDEDED"}
                    fontSize={10}
                    fontFamily="'JetBrains Mono', monospace"
                    fontWeight={isSelected ? "bold" : "normal"}
                    pointerEvents="none"
                    className="select-none uppercase tracking-wider"
                  >
                    {n.name}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>

      {/* Selected / Hovered Node Telemetry Drawer */}
      {(selectedNode || hoveredNode) && (
        <div className="mt-2 p-3 bg-[#15161D] border border-white/[0.1] text-xs relative z-10 animate-in fade-in duration-150">
          <div className="flex items-center justify-between font-mono font-semibold">
            <span className="flex items-center gap-1.5 text-[#FA3600] uppercase">
              <span>+</span>
              {(hoveredNode || selectedNode)?.name}
            </span>
            <span className="heron-tag-brand text-[9px]">
              DOMAIN: {(hoveredNode || selectedNode)?.domain || "GENERAL"}
            </span>
          </div>
          {(hoveredNode || selectedNode)?.summary && (
            <p className="mt-1 text-[#8C8C88] text-[11px] font-sans leading-relaxed">
              {(hoveredNode || selectedNode)?.summary}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
