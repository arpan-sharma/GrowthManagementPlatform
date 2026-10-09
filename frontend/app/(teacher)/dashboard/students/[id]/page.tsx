"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ChapterTopicList } from "@/components/students/ChapterTopicList";
import { SubjectCard } from "@/components/students/SubjectCard";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { Tag } from "@/components/ui/Tag";
import { fetchStudentProfile, type StudentProfile } from "@/lib/api";
import { formatInr, formatShortDate, initials } from "@/lib/format";

const FEE_TONE = { Paid: "good", Partial: "warn", Overdue: "bad" } as const;

export default function StudentProfilePage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    fetchStudentProfile(params.id)
      .then((data) => {
        if (active) setProfile(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Could not load student.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [params.id]);

  if (loading) return <p className="text-[13px] text-text-muted">Loading student profile…</p>;
  if (error) return <p className="text-[13px] text-danger">{error}</p>;
  if (!profile) return <p>Student not found.</p>;

  const { student, subjects, chapters, fee } = profile;
  const subjectName = chapters[0]?.subject;

  return (
    <div>
      <Link href="/dashboard/students" className={`${buttonClass()} mb-4`}>
        ← Back to students
      </Link>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3.5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-[52px] w-[52px] items-center justify-center rounded-full bg-accent-bg text-[17px] font-semibold text-accent-strong">
            {initials(student.name)}
          </div>
          <div>
            <h2 className="m-0 text-lg font-semibold">{student.name}</h2>
            <p className="m-0 mt-0.5 text-[13px] text-text-muted">
              Batch {student.batchId} · Parent: {student.parentPhone || "—"}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" className={buttonClass()}>
            Call parent
          </button>
          <button type="button" className={buttonClass("primary")}>
            Send report
          </button>
        </div>
      </div>
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile value={`${student.attendancePct}%`} label="Overall attendance" />
        <StatTile value={student.overallAverage === null ? "—" : `${student.overallAverage}%`} label="Overall average" />
        <StatTile value={student.today ?? "—"} label="Today's status" />
        <StatTile value={student.feeStatus ?? "—"} label="Fee status" />
      </div>
      {student.flagReason && (
        <div className="mb-5 rounded-xl border border-danger bg-danger-bg p-4 text-[13px]">
          <b className="text-danger">Flag reason:</b> {student.flagReason}
        </div>
      )}
      <h2 className="mb-3 mt-6 text-sm font-semibold">Subjects</h2>
      {subjects.length === 0 ? (
        <p className="text-[13px] text-text-muted">No subject scores yet.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-3">
          {subjects.map((score) => (
            <SubjectCard key={score.subject} score={score} />
          ))}
        </div>
      )}
      {chapters.length > 0 && subjectName && (
        <>
          <h2 className="mb-3 mt-6 text-sm font-semibold">Chapter & topic analysis — {subjectName}</h2>
          <ChapterTopicList chapters={chapters} />
        </>
      )}
      <h2 className="mb-3 mt-6 text-sm font-semibold">Fees</h2>
      <Card>
        {fee ? (
          <span className="text-[13.5px]">
            Paid {formatInr(fee.paid)} of {formatInr(fee.paid + fee.balance)} · Due date {formatShortDate(fee.dueDate)} ·{" "}
            <Tag tone={FEE_TONE[fee.status]}>{fee.status}</Tag>
          </span>
        ) : (
          <span className="text-[13.5px] text-text-muted">No fee record.</span>
        )}
      </Card>
    </div>
  );
}
