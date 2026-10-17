"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  fetchSessionGraph,
  submitAnswer,
  endSession,
  startSession,
  resetDemo,
  Problem,
  GraphView,
  MemoryDiff,
} from "../../lib/api";
import { DemoBar } from "../../components/DemoBar";
import { ChildStage } from "../../components/ChildStage";
import { WhyPanel } from "../../components/WhyPanel";
import { SettingsModal } from "../../components/SettingsModal";

function LearnSessionContent() {
  const router = useRouter();
  const routeParams = useParams();
  const sessionId = (routeParams?.sessionId as string) || "";

  const [childId, setChildId] = useState("leo");
  const [childName, setChildName] = useState("Leo");
  const [dayLabel, setDayLabel] = useState("Day 1");
  const [graphMode, setGraphMode] = useState<"on" | "off">("on");

  // Problem and Stage State
  const [problem, setProblem] = useState<Problem>({
    problem_id: "init",
    skill_id: "count_on",
    op: "+",
    a: 3,
    b: 4,
    answer: 7,
    story_slots: { object_set: "space", a: 3, b: 4, op: "+" },
  });
  const [story, setStory] = useState(
    "Welcome to the space launch! Let's load the shiny rockets."
  );
  const [tutorText, setTutorText] = useState(
    "Touch the rockets on screen and tell me how many you count in all!"
  );
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [turnCount, setTurnCount] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSessionActive, setIsSessionActive] = useState(true);

  // Why Panel State
  const [graphData, setGraphData] = useState<GraphView | null>(null);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [memoryDiff, setMemoryDiff] = useState<MemoryDiff | null>(null);

  // Settings
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Initialize from localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const cid = localStorage.getItem("primer_active_child_id") || "leo";
      const cname = localStorage.getItem("primer_active_child_name") || "Leo";
      const dlabel = localStorage.getItem("primer_day_label") || "Day 1";
      setChildId(cid);
      setChildName(cname);
      setDayLabel(dlabel);
    }
    loadGraph();
  }, [sessionId]);

  const loadGraph = async () => {
    try {
      if (graphMode === "on") {
        const g = await fetchSessionGraph(sessionId);
        setGraphData(g);
      } else {
        setGraphData(null);
      }
    } catch (err) {
      console.warn("Could not load session graph", err);
    }
  };

  // Handle child submitting an answer
  const handleAnswer = async (given: number, freeText?: string) => {
    if (!isSessionActive) return;
    setIsSubmitting(true);
    try {
      const res = await submitAnswer(sessionId, problem.problem_id, given, freeText);
      setIsCorrect(res.correct);
      setTutorText(res.tutor_text);

      // Add recorded decision if any
      if (res.decision_ids && res.decision_ids.length > 0) {
        const newDecisions = res.decision_ids.map((id) => ({
          id,
          kind: res.kind,
          summary: res.tutor_text,
          memory_used: res.kind === "hint" ? ["procedural", "working"] : ["working"],
        }));
        setDecisions((prev) => [...prev, ...newDecisions]);
      }

      // If correct and next problem provided, advance to it
      if (res.correct && res.next_problem) {
        setTurnCount((prev) => prev + 1);
        setProblem(res.next_problem);
        setStory("Great job! Here is your next challenge:");
      }

      // Refresh graph view
      await loadGraph();
    } catch (err) {
      console.error("Answer submission failed", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // End Session & Consolidate
  const handleEndSession = async () => {
    try {
      const diff = await endSession(sessionId);
      setMemoryDiff(diff);
      setIsSessionActive(false);
      setTutorText("You finished your session! High five for doing math today!");
    } catch (err) {
      console.error("End session failed", err);
    }
  };

  // Next Day (Day 2 progression)
  const handleNextDay = async () => {
    try {
      const nextDayLabel = "Day 2";
      localStorage.setItem("primer_day_label", nextDayLabel);
      setDayLabel(nextDayLabel);

      const res = await startSession(childId, graphMode);
      router.push(`/learn/${res.session_id}`);
    } catch (err) {
      console.error("Failed to start next day session", err);
    }
  };

  // Reset Demo
  const handleResetDemo = async () => {
    try {
      await resetDemo();
      localStorage.setItem("primer_day_label", "Day 1");
      router.push("/");
    } catch (err) {
      console.error("Reset failed", err);
    }
  };

  // Toggle Graph Mode
  const handleToggleGraphMode = () => {
    const nextMode = graphMode === "on" ? "off" : "on";
    setGraphMode(nextMode);
    if (nextMode === "off") {
      setGraphData(null);
    } else {
      loadGraph();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F4ED] font-child">
      {/* Top Demo Bar */}
      <DemoBar
        dayLabel={dayLabel}
        graphMode={graphMode}
        onToggleGraphMode={handleToggleGraphMode}
        onEndSession={handleEndSession}
        onNextDay={handleNextDay}
        onResetDemo={handleResetDemo}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isSessionActive={isSessionActive}
      />

      {/* Main Split: Child Stage (Left) & Why Panel (Right) */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Child Stage Surface */}
        <ChildStage
          childName={childName}
          problem={problem}
          story={story}
          tutorText={tutorText}
          isCorrect={isCorrect}
          turnCount={turnCount}
          onAnswer={handleAnswer}
          isSubmitting={isSubmitting}
        />

        {/* Why Panel Surface */}
        <WhyPanel
          graphMode={graphMode}
          graphData={graphData}
          decisions={decisions}
          memoryDiff={memoryDiff}
          sessionId={sessionId}
          onRefreshGraph={loadGraph}
        />
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}

export default function LearnSessionPage() {
  return (
    <Suspense
      fallback={
        <div className="h-screen w-screen flex items-center justify-center bg-[#F7F4ED] font-mono text-sm text-[#4A4A6A]">
          Loading MentoAI Learning Session...
        </div>
      }
    >
      <LearnSessionContent />
    </Suspense>
  );
}
