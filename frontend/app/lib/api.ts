/**
 * frontend/app/lib/api.ts — API client for MentoAI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface Persona {
  id: string;
  name: string;
  summary: string;
  topics: string[];
  register: string;
}

export interface MindNode {
  id?: string;
  key?: string;
  name: string;
  domain: string;
  depth?: number;
  confidence?: number;
  summary?: string;
}

export interface MindEdge {
  source: string;
  target: string;
  type: string;
  why?: string;
  confidence?: number;
}

export interface MindGraph {
  nodes: MindNode[];
  edges: MindEdge[];
}

export interface DecisionTraceItem {
  id: string;
  agent: string;
  kind: string;
  chosen_move: string;
  rationale: string;
  confidence: number;
  ts: number;
}

export interface DecisionTrace {
  decision: DecisionTraceItem | null;
  chosen_target: string | null;
  turn_text: string | null;
  because_items: Array<{ type: string; note: string; target_id?: string; text?: string }>;
  teaching_moves: string[];
}

export interface DigestItem {
  id: string;
  text: string;
  topics: string[];
  strengths: string[];
  shaky_areas: string[];
  offline_activities: string[];
  ts: number;
}

export interface DigestResponse {
  learner_id: string;
  digests: DigestItem[];
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await fetch(`${API_BASE}/personas`);
  if (!res.ok) throw new Error("Failed to fetch personas");
  return res.json();
}

export async function restorePersona(personaId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/personas/${personaId}/restore`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to restore persona memory");
  return res.json();
}

export async function createLearner(displayName: string, registerText: string = "curious explorer"): Promise<{ learner_id: string }> {
  const res = await fetch(`${API_BASE}/learners`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: displayName, register_text: registerText }),
  });
  if (!res.ok) throw new Error("Failed to create learner");
  return res.json();
}

export async function forgetLearner(learnerId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/learners/${learnerId}/forget`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to forget learner");
  return res.json();
}

export async function startConversation(learnerId: string, title: string = "Exploration"): Promise<{ conversation_id: string }> {
  const res = await fetch(`${API_BASE}/learners/${learnerId}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to start conversation");
  return res.json();
}

export async function fetchMindGraph(learnerId: string): Promise<MindGraph> {
  const res = await fetch(`${API_BASE}/learners/${learnerId}/mind`);
  if (!res.ok) throw new Error("Failed to fetch mind graph");
  return res.json();
}

export async function fetchDecisionTrace(decisionId: string): Promise<DecisionTrace> {
  const res = await fetch(`${API_BASE}/decisions/${decisionId}/trace`);
  if (!res.ok) throw new Error("Failed to fetch decision trace");
  return res.json();
}

export async function fetchDigest(learnerId: string): Promise<DigestResponse> {
  const res = await fetch(`${API_BASE}/learners/${learnerId}/digest`);
  if (!res.ok) throw new Error("Failed to fetch grown-up digest");
  return res.json();
}

export async function getGraphMode(): Promise<{ graph_mode_enabled: boolean }> {
  const res = await fetch(`${API_BASE}/admin/graph-mode`);
  if (!res.ok) throw new Error("Failed to get graph mode");
  return res.json();
}

export async function setGraphMode(enabled: boolean): Promise<any> {
  const res = await fetch(`${API_BASE}/admin/graph-mode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error("Failed to set graph mode");
  return res.json();
}
