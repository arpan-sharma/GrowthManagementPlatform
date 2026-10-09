"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles } from "lucide-react";
import { AssistantPanel } from "./AssistantPanel";
import { Brand } from "./Brand";
import { Tabs } from "./Tabs";

const TABS = [
  { id: "/dashboard", label: "Overview", href: "/dashboard" },
  { id: "/dashboard/students", label: "Students", href: "/dashboard/students" },
  { id: "/dashboard/tests", label: "Tests", href: "/dashboard/tests" },
  { id: "/dashboard/fees", label: "Fees", href: "/dashboard/fees" },
];

function activeTab(pathname: string): string {
  if (pathname.startsWith("/dashboard/students")) return "/dashboard/students";
  if (pathname.startsWith("/dashboard/tests")) return "/dashboard/tests";
  if (pathname.startsWith("/dashboard/fees")) return "/dashboard/fees";
  return "/dashboard";
}

export function Navbar() {
  const pathname = usePathname();
  const [assistantOpen, setAssistantOpen] = useState(false);

  return (
    <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-border bg-surface px-5 py-3.5">
      <Brand />
      <Tabs tabs={TABS} active={activeTab(pathname)} />
      <div className="relative flex items-center gap-2.5">
        <button
          type="button"
          title="Ask AI assistant"
          aria-expanded={assistantOpen}
          onClick={() => setAssistantOpen((open) => !open)}
          className="flex h-[38px] w-[38px] items-center justify-center rounded-full bg-accent text-white"
        >
          <Sparkles size={16} />
        </button>
        {assistantOpen && <AssistantPanel onClose={() => setAssistantOpen(false)} />}
        <Link
          href="/login"
          title="Log out"
          className="flex h-[34px] w-[34px] items-center justify-center rounded-full border border-border bg-surface-muted text-xs font-semibold text-text-muted"
        >
          RS
        </Link>
      </div>
    </header>
  );
}
