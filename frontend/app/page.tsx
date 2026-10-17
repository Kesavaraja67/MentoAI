"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  fetchPersonas,
  restorePersona,
  fetchMindGraph,
  fetchDigest,
  getGraphMode,
  setGraphMode,
  forgetLearner,
  startConversation,
  Persona,
  MindGraph,
  DigestItem,
} from "./lib/api";
import { SpatialGrid } from "./components/SpatialGrid";
import { TopBar } from "./components/TopBar";
import { VoiceCore } from "./components/VoiceCore";
import { LiveSubtitles } from "./components/LiveSubtitles";
import { ConstellationMind } from "./components/ConstellationMind";
import { WhyPanel } from "./components/WhyPanel";
import { VisualStage } from "./components/VisualStage";
import { DigestModal } from "./components/DigestModal";
import { ArrowRight } from "@phosphor-icons/react";

export default function MentoAIMainPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [currentPersonaId, setCurrentPersonaId] = useState<string>("mira");
  const [conversationId, setConversationId] = useState<string>("");
  const [state, setState] = useState<"listening" | "thinking" | "speaking">("listening");
  const [isMuted, setIsMuted] = useState<boolean>(true);
  const [textInput, setTextInput] = useState<string>("");

  // Subtitles & Visuals
  const [personText, setPersonText] = useState<string>("");
  const [isPersonFinal, setIsPersonFinal] = useState<boolean>(true);
  const [mentoaiText, setMentoaiText] = useState<string>("");
  const [activeVisual, setActiveVisual] = useState<any | null>(null);

  // Graph and Trace
  const [mindData, setMindData] = useState<MindGraph | null>(null);
  const [activePulsingKey, setActivePulsingKey] = useState<string | null>(null);
  const [latestDecisionId, setLatestDecisionId] = useState<string | null>(null);

  // Digest and Admin
  const [digests, setDigests] = useState<DigestItem[]>([]);
  const [isDigestOpen, setIsDigestOpen] = useState<boolean>(false);
  const [graphModeEnabled, setGraphModeEnabledState] = useState<boolean>(true);

  // WebSocket Ref
  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Personas & Restore Default
  useEffect(() => {
    fetchPersonas()
      .then((data) => {
        setPersonas(data);
        handleSwitchPersona("mira");
      })
      .catch((err) => console.error("Error loading personas:", err));

    getGraphMode()
      .then((res) => setGraphModeEnabledState(res.graph_mode_enabled))
      .catch((err) => console.error("Error loading graph mode:", err));

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  // Connect WebSocket when conversationId changes
  useEffect(() => {
    if (!conversationId) return;

    const wsUrl = `ws://localhost:8000/ws/conversations/${conversationId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "hello", learner_id: currentPersonaId, mode: "A" }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "state") {
          setState(msg.state);
        } else if (msg.type === "subtitle.person") {
          setPersonText(msg.text);
          setIsPersonFinal(msg.final);
        } else if (msg.type === "subtitle.mentoai") {
          setMentoaiText((prev) => (prev ? `${prev} ${msg.delta}` : msg.delta));
        } else if (msg.type === "tts.text") {
          speakAloud(msg.text);
        } else if (msg.type === "visual") {
          setActiveVisual(msg);
        } else if (msg.type === "decision") {
          setLatestDecisionId(msg.id);
        } else if (msg.type === "viz.event") {
          handleVizEvent(msg);
        }
      } catch (err) {
        console.error("Error parsing WS message:", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [conversationId, currentPersonaId]);

  // Handle incoming graph updates
  const handleVizEvent = (msg: any) => {
    if (msg.op === "pulse" && msg.payload?.concept) {
      setActivePulsingKey(msg.payload.concept);
      setTimeout(() => setActivePulsingKey(null), 3000);
    } else if (msg.op === "mind_refresh" || msg.op === "add_node") {
      fetchMindGraph(currentPersonaId).then((g) => setMindData(g));
    }
  };

  // Switch Persona and Restore Graph
  const handleSwitchPersona = async (personaId: string) => {
    setCurrentPersonaId(personaId);
    setMentoaiText("");
    setPersonText("");
    setActiveVisual(null);
    setLatestDecisionId(null);

    try {
      await restorePersona(personaId);
      const conv = await startConversation(personaId, "Live Exploration");
      setConversationId(conv.conversation_id);
      const mind = await fetchMindGraph(personaId);
      setMindData(mind);
      const dig = await fetchDigest(personaId);
      setDigests(dig.digests || []);
    } catch (err) {
      console.error("Failed to restore persona:", err);
    }
  };

  // High-Fidelity Human-Like Voice Selection (100% Free Chrome/Edge Neural Voices)
  const getHumanVoice = (): SpeechSynthesisVoice | null => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return null;
    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return null;

    // Prioritize natural neural conversational voices
    const naturalVoice =
      voices.find((v) => v.name.includes("Jenny") && v.name.includes("Natural")) ||
      voices.find((v) => v.name.includes("Aria") && v.name.includes("Natural")) ||
      voices.find((v) => v.name.includes("Natural") && v.lang.startsWith("en")) ||
      voices.find((v) => v.name.includes("Google") && v.lang.startsWith("en")) ||
      voices.find((v) => v.name.includes("Guy") && v.name.includes("Natural")) ||
      voices.find((v) => v.lang === "en-US" && !v.name.includes("Desktop")) ||
      voices.find((v) => v.lang.startsWith("en")) ||
      voices[0];

    return naturalVoice || null;
  };

  // Browser Speech Synthesis with Human Inflection
  const speakAloud = (text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const cleanText = text.replace(/[*_#`~[\]]/g, "").trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const humanVoice = getHumanVoice();
    if (humanVoice) {
      utterance.voice = humanVoice;
    }
    // Warm, relaxed, human conversational cadence
    utterance.rate = 0.96;
    utterance.pitch = 1.04;

    utterance.onend = () => {
      setState("listening");
    };

    window.speechSynthesis.speak(utterance);
  };

  // Browser Speech Recognition (Mode A)
  const toggleSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is supported in Chrome/Edge browsers. You can also type below.");
      return;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
      setIsMuted(true);
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = (event: any) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      // If user speaks, instantly quiet the AI (active listener behavior)
      if (interim && typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }

      if (interim && wsRef.current) {
        wsRef.current.send(JSON.stringify({ type: "transcript.partial", text: interim }));
      }
      if (final && wsRef.current) {
        setMentoaiText("");
        wsRef.current.send(JSON.stringify({ type: "transcript.final", text: final }));
      }
    };

    rec.onerror = (e: any) => {
      console.warn("Speech recognition error:", e);
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        alert("Microphone permission was blocked. Please click the lock/settings icon in your browser address bar to allow microphone access, then refresh.");
      }
      setIsMuted(true);
      recognitionRef.current = null;
    };
    rec.onend = () => {
      setIsMuted(true);
      recognitionRef.current = null;
    };

    try {
      rec.start();
      recognitionRef.current = rec;
      setIsMuted(false);
    } catch (err) {
      console.error("Could not start recognition:", err);
      setIsMuted(true);
    }
  };

  // Submit Text Fallback Turn
  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || !wsRef.current) return;
    // Silence previous speech immediately
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setMentoaiText("");
    wsRef.current.send(JSON.stringify({ type: "transcript.final", text: textInput.trim() }));
    setTextInput("");
  };

  // Interruption / Barge-in
  const handleBargeIn = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: "barge_in", spoken_chars: 0 }));
    }
    setState("listening");
  };

  // Rule 3 Graph Mode Toggle
  const handleToggleGraphMode = async (enabled: boolean) => {
    setGraphModeEnabledState(enabled);
    await setGraphMode(enabled);
    if (!enabled) {
      setMindData({ nodes: [], edges: [] });
    } else {
      fetchMindGraph(currentPersonaId).then((g) => setMindData(g));
    }
  };

  // Forget Learner (Rule 6 Privacy)
  const handleForgetLearner = async () => {
    if (confirm("Are you sure you want to forget this learner and wipe their FalkorDB graph memory?")) {
      await forgetLearner(currentPersonaId);
      setMindData({ nodes: [], edges: [] });
      setMentoaiText("");
      setPersonText("");
      alert("Graph memory completely erased.");
    }
  };

  return (
    <div className="relative min-h-screen bg-[#090A0D] text-[#EDEDED] flex flex-col font-sans select-none overflow-x-hidden">
      {/* 3D Perspective Wireframe Horizon Background (Awwwards WebGL Engine) */}
      <SpatialGrid state={state} />

      {/* Heron AI Architectural Navigation Header */}
      <TopBar
        personas={personas}
        currentPersonaId={currentPersonaId}
        onSelectPersona={handleSwitchPersona}
        graphModeEnabled={graphModeEnabled}
        onToggleGraphMode={handleToggleGraphMode}
        onOpenDigest={() => setIsDigestOpen(true)}
        onForgetLearner={handleForgetLearner}
      />

      {/* Main Architectural Cockpit Grid */}
      <main className="relative z-10 flex-1 px-4 md:px-8 py-4 grid grid-cols-1 lg:grid-cols-12 gap-5 max-w-[1680px] w-full mx-auto">
        {/* Left Column: Voice Core Oscillator & Dialogue Transcript (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          {/* 3D Wireframe Audio Oscillator Stage */}
          <div className="heron-panel p-2 crosshair-tl crosshair-tr relative overflow-hidden">
            <VoiceCore
              state={state}
              isMuted={isMuted}
              onToggleMute={toggleSpeechRecognition}
              onClickOrb={toggleSpeechRecognition}
              onBargeIn={handleBargeIn}
            />
          </div>

          {/* Real-time Subtitles Feed */}
          <LiveSubtitles
            personText={personText}
            isPersonFinal={isPersonFinal}
            mentoaiText={mentoaiText}
            state={state}
          />

          {/* Visual Memory Card if Active */}
          <VisualStage card={activeVisual} onDismiss={() => setActiveVisual(null)} />

          {/* Architectural Command Terminal Input */}
          <form
            onSubmit={handleSendText}
            className="heron-panel p-1.5 flex items-center gap-2 border border-white/[0.12] bg-[#0E0F14] focus-within:border-[#FA3600]"
          >
            <span className="font-mono text-xs text-[#FA3600] pl-3 font-bold">{">"}</span>
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="TRANSMIT QUERY // EXPLORE CONCEPT..."
              className="flex-1 bg-transparent px-2 py-2 text-xs font-mono text-white placeholder-[#5C5C58] focus:outline-none uppercase tracking-wider"
            />
            <button
              type="submit"
              disabled={!textInput.trim()}
              className="heron-btn-brand px-3.5 py-2 text-xs flex items-center gap-1 cursor-pointer disabled:opacity-30 disabled:hover:bg-[#FA3600] disabled:hover:text-white"
              title="Transmit query"
            >
              <span>SEND</span>
              <ArrowRight size={14} weight="bold" />
            </button>
          </form>
        </div>

        {/* Right Column: Constellation Mind Graph & Reasoning Dossier (7 cols) */}
        <div className="lg:col-span-7 grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
          {/* Constellation Mind Graph */}
          <div className="h-full">
            <ConstellationMind
              mindData={mindData}
              activePulsingKey={activePulsingKey}
              onSelectNode={(node) => console.log("Selected node:", node)}
            />
          </div>

          {/* Why Panel Reasoning Dossier */}
          <div className="h-full">
            <WhyPanel latestDecisionId={latestDecisionId} />
          </div>
        </div>
      </main>

      {/* Grown-Up Learning Digest Modal */}
      <DigestModal
        isOpen={isDigestOpen}
        onClose={() => setIsDigestOpen(false)}
        digests={digests}
      />
    </div>
  );
}
