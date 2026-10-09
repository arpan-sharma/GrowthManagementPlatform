"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ClipboardList, FilePlus, Receipt, UserPlus } from "lucide-react";
import { AttendanceRing } from "@/components/dashboard/AttendanceRing";
import { FlagList } from "@/components/dashboard/FlagList";
import { NoticeBoard } from "@/components/dashboard/NoticeBoard";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { fetchDashboard } from "@/lib/api";
import { readSessionUser } from "@/lib/auth";
import { formatLongDate } from "@/lib/format";
import type { Student } from "@/lib/types";

type DashboardData = Awaited<ReturnType<typeof fetchDashboard>>;

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const user = readSessionUser();
    setName(user ? `${user.first_name} ${user.last_name}`.trim() : "");
    fetchDashboard()
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load dashboard."));
  }, []);

  const flagged: Student[] = data?.flagged.map((row) => ({
    id: row.id,
    name: `${row.first_name} ${row.last_name}`.trim(),
    batchId: row.batch_id,
    batchName: row.batch_name,
    parentPhone: row.contact_number,
    parentEmail: row.email ?? undefined,
    attendancePct: row.attendance_pct,
    overallAverage: row.overall_average,
    previousOverallAverage: row.previous_overall_average,
    feeStatus: row.fee_status,
    flagged: row.flagged,
    flagReason: row.flag_reason ?? undefined,
    today: row.today,
  })) ?? [];

  if (error) return <p role="alert" className="text-danger">{error}</p>;
  if (!data) return <p className="text-text-muted">Loading overview…</p>;

  const today = new Date().toISOString().slice(0, 10);
  const greeting = new Date().getHours() < 12 ? "Good morning" : new Date().getHours() < 18 ? "Good afternoon" : "Good evening";
  return (
    <div>
      <p className="m-0 text-[13px] text-text-faint">{formatLongDate(today)}</p>
      <h1 className="m-0 mt-1 text-[22px] font-semibold">{greeting}{name ? `, ${name}` : ""}</h1>
      <p className="mb-5 mt-2 max-w-[620px] text-[14.5px] leading-relaxed text-text-muted">
        <b className="text-text">{data.attendance_pct}% attendance</b> across <b className="text-text">{data.batch_count} batches</b>.
      </p>
      <Card className="mb-5 grid items-center gap-4 sm:grid-cols-[120px_1fr]">
        <AttendanceRing percent={data.attendance_pct} />
        <div className="grid grid-cols-2 gap-2.5">
          <div><p className="m-0 text-[19px] font-semibold">{data.batch_count}</p><p className="m-0 mt-0.5 text-xs text-text-muted">batches</p></div>
          <div><p className="m-0 text-[19px] font-semibold">{data.student_count}</p><p className="m-0 mt-0.5 text-xs text-text-muted">students</p></div>
        </div>
      </Card>
      <FlagList students={flagged} />
      <h2 className="mb-3 mt-6 text-sm font-semibold">Notice board</h2>
      <NoticeBoard notices={data.notices.map((notice) => ({ id: notice.id, text: notice.content || notice.title, postedAt: notice.date ?? "", batchId: "All" }))} />
      <h2 className="mb-3 mt-6 text-sm font-semibold">Quick actions</h2>
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <Link href="/dashboard/attendance" className={buttonClass()}><ClipboardList size={14} className="mr-1.5" /> Mark attendance</Link>
        <Link href="/dashboard/students/new" className={buttonClass()}><UserPlus size={14} className="mr-1.5" /> Add student</Link>
        <Link href="/dashboard/tests/create" className={buttonClass()}><FilePlus size={14} className="mr-1.5" /> Create test</Link>
        <Link href="/dashboard/fees" className={buttonClass()}><Receipt size={14} className="mr-1.5" /> Fees</Link>
      </div>
    </div>
  );
}
