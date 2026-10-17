"use client";

import React, { useState, useEffect } from "react";
import { X, Key, Cpu, ShieldCheck } from "@phosphor-icons/react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PROVIDERS = [
  { id: "openai", name: "OpenAI", defaultModel: "gpt-4o-mini" },
  { id: "groq", name: "Groq (Fast)", defaultModel: "llama-3.3-70b-versatile" },
  { id: "openrouter", name: "OpenRouter", defaultModel: "meta-llama/llama-3.3-70b-instruct" },
  { id: "gemini", name: "Google Gemini", defaultModel: "gemini-1.5-flash" },
];

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o-mini");
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const p = localStorage.getItem("primer_byok_provider") || "openai";
      const m = localStorage.getItem("primer_byok_model") || "gpt-4o-mini";
      const k = localStorage.getItem("primer_byok_key") || "";
      setProvider(p);
      setModel(m);
      setApiKey(k);
    }
  }, [isOpen]);

  const handleProviderChange = (newProv: string) => {
    setProvider(newProv);
    const matched = PROVIDERS.find((p) => p.id === newProv);
    if (matched) {
      setModel(matched.defaultModel);
    }
  };

  const handleSave = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("primer_byok_provider", provider);
      localStorage.setItem("primer_byok_model", model);
      localStorage.setItem("primer_byok_key", apiKey.trim());
      setSaved(true);
      setTimeout(() => {
        setSaved(false);
        onClose();
      }, 700);
    }
  };

  const handleClear = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("primer_byok_provider");
      localStorage.removeItem("primer_byok_model");
      localStorage.removeItem("primer_byok_key");
      setApiKey("");
      setProvider("openai");
      setModel("gpt-4o-mini");
      setSaved(true);
      setTimeout(() => {
        setSaved(false);
        onClose();
      }, 700);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
    >
      <div className="w-full max-w-md rounded-2xl bg-[#FFFFFF] p-6 shadow-2xl border-2 border-[#CDD2DB] text-[#1E2532]">
        <div className="flex items-center justify-between pb-4 border-b border-[#CDD2DB]">
          <div className="flex items-center gap-2">
            <Key size={24} weight="bold" className="text-[#2D9CDB]" />
            <h2 className="text-xl font-bold font-sans">BYOK Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 hover:bg-[#F0F2F5] transition-colors"
            aria-label="Close settings"
          >
            <X size={20} weight="bold" />
          </button>
        </div>

        <p className="mt-3 text-sm text-[#5A6478]">
          Bring your own API key to test live wording. Keys are sent only in headers over HTTPS and are never stored or logged by the server.
        </p>

        <div className="mt-5 space-y-4 text-sm font-sans">
          <div>
            <label className="block font-semibold mb-1 text-xs uppercase tracking-wider text-[#5A6478]">
              LLM Provider (Allowlist)
            </label>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full rounded-xl border border-[#CDD2DB] bg-[#F0F2F5] p-3 font-medium text-[#1E2532] focus:border-[#2D9CDB] focus:bg-[#FFFFFF]"
            >
              {PROVIDERS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold mb-1 text-xs uppercase tracking-wider text-[#5A6478]">
              Model Name
            </label>
            <div className="flex items-center gap-2 rounded-xl border border-[#CDD2DB] bg-[#F0F2F5] px-3 focus-within:border-[#2D9CDB] focus-within:bg-[#FFFFFF]">
              <Cpu size={18} className="text-[#5A6478]" />
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="gpt-4o-mini"
                className="w-full py-3 bg-transparent text-[#1E2532] outline-none font-mono text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold mb-1 text-xs uppercase tracking-wider text-[#5A6478]">
              API Key (Optional)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Leave empty for deterministic offline demo"
              className="w-full rounded-xl border border-[#CDD2DB] bg-[#F0F2F5] p-3 text-[#1E2532] font-mono text-xs focus:border-[#2D9CDB] focus:bg-[#FFFFFF]"
            />
          </div>

          <div className="flex items-center gap-2 rounded-xl bg-[#EDF7ED] p-3 text-xs text-[#2E7D32]">
            <ShieldCheck size={20} weight="bold" />
            <span>If key is blank, Primer runs in deterministic offline demo mode.</span>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between gap-3 pt-4 border-t border-[#CDD2DB]">
          <button
            onClick={handleClear}
            className="text-xs font-semibold text-[#5A6478] hover:text-[#1E2532] underline"
          >
            Clear Stored Key
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="rounded-xl px-4 py-2.5 font-semibold text-sm hover:bg-[#F0F2F5] text-[#5A6478]"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="rounded-xl bg-[#2D9CDB] px-5 py-2.5 font-semibold text-sm text-white hover:bg-[#2582b8] transition-colors shadow-sm"
            >
              {saved ? "Saved!" : "Save Settings"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
