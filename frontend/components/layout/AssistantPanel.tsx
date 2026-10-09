"use client";

import { useEffect, useState } from "react";
import { Sparkles, X } from "lucide-react";
import { replyTo } from "@/lib/assistant";
import { fetchNotices, fetchStudents, fetchTests } from "@/lib/api";
import { getFees } from "@/lib/data/fees";
import type { FeeRecord, Notice, Student, Test } from "@/lib/types";

type Message = { from: "user" | "assistant"; text: string };

const WELCOME: Message = {
  from: "assistant",
  text: "Ask about a student, flags, fees, attendance, tests, or notices. I only use the records on this page.",
};

export function AssistantPanel({ onClose }: { onClose: () => void }) {
  const [facts, setFacts] = useState<{ students: Student[]; fees: FeeRecord[]; tests: Test[]; notices: Notice[] }>({ students: [], fees: [], tests: [], notices: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    Promise.all([fetchStudents(), getFees(), fetchTests(), fetchNotices()])
      .then(([students, rows, tests, notices]) => setFacts({
        students,
        fees: rows,
        tests,
        notices,
      }))
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load class records."))
      .finally(() => setLoading(false));
  }, []);

  function send() {
    const question = draft.trim();
    if (!question) return;
    const answer = loading ? "Class records are still loading. Please try again in a moment." : error ? "I couldn't load the latest class records. Please reopen the assistant and try again." : replyTo(question, facts);
    setMessages((current) => [...current, { from: "user", text: question }, { from: "assistant", text: answer }]);
    setDraft("");
  }

  return (
    <div className="absolute right-0 top-12 z-20 flex h-[440px] w-[340px] flex-col overflow-hidden rounded-xl border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-3.5 py-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-white">
            <Sparkles size={14} />
          </span>
          Assistant
        </div>
        <button type="button" onClick={onClose} className="text-text-muted" aria-label="Close assistant">
          <X size={16} />
        </button>
      </div>
      <div className="flex flex-1 flex-col gap-2.5 overflow-y-auto px-3.5 py-3">
        {loading && <p className="m-0 text-xs text-text-muted">Loading class records…</p>}
        {messages.map((message, index) => (
          <p
            key={index}
            className={`m-0 max-w-[85%] whitespace-pre-wrap rounded-[10px] px-3 py-2 text-[13px] leading-relaxed ${
              message.from === "user" ? "self-end bg-accent-bg text-accent-strong" : "self-start bg-surface-muted text-text"
            }`}
          >
            {message.text}
          </p>
        ))}
      </div>
      <form
        className="flex gap-2 border-t border-border p-3"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
      >
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask a question"
          className="flex-1"
        />
        <button type="submit" className="rounded-lg bg-accent px-3 text-[13px] font-medium text-white">
          Send
        </button>
      </form>
    </div>
  );
}
