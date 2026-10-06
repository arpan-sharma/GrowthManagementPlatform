"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { fetchAttendanceSession, fetchBatches, fetchSubjects, saveAttendanceSession } from "@/lib/api";
import type { TodayStatus } from "@/lib/types";

const OPTIONS: TodayStatus[] = ["Present", "Late", "Absent"];

export default function AttendancePage() {
  const [batchId, setBatchId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [batchName, setBatchName] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [onDate, setOnDate] = useState("");
  const [rows, setRows] = useState<{ studentId: string; name: string }[]>([]);
  const [marks, setMarks] = useState<Record<string, TodayStatus>>({});
  const [batches, setBatches] = useState<{ id: string; name: string }[]>([]);
  const [subjects, setSubjects] = useState<{ id: string; name: string }[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([fetchBatches(), fetchSubjects()])
      .then(([batchRows, subjectRows]) => {
        if (!active) return;
        setBatches(batchRows);
        setSubjects(subjectRows);
        const firstBatch = batchRows[0]?.id ?? "";
        const firstSubject = subjectRows[0]?.id ?? "";
        setBatchId(firstBatch);
        setSubjectId(firstSubject);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Could not load attendance session.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!batchId || !subjectId) return;
    let active = true;
    setError("");
    fetchAttendanceSession(batchId, subjectId)
      .then((session) => {
        if (!active) return;
        setBatchName(session.batchName);
        setSubjectName(session.subjectName);
        setOnDate(session.onDate);
        setRows(session.students.map((row) => ({ studentId: row.studentId, name: row.name })));
        setMarks(
          Object.fromEntries(
            session.students.map((row) => [row.studentId, row.status ?? "Present"]),
          ),
        );
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Could not load attendance session.");
      });
  }, [batchId, subjectId]);

  async function submit() {
    if (!batchId || !subjectId) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      await saveAttendanceSession(batchId, subjectId, marks, onDate || undefined);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save attendance.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-[13px] text-text-muted">Loading attendance…</p>;

  return (
    <div>
      <Link href="/dashboard" className={`${buttonClass()} mb-4`}>
        ← Back
      </Link>
      <h1 className="m-0 text-[21px] font-semibold">Mark attendance</h1>
      <p className="mb-4 mt-1.5 text-[13px] text-text-muted">
        {subjectName || "Subject"} · {batchName || "Batch"} · {onDate || "Today"}
      </p>
      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <label className="block text-[12.5px] text-text-muted">
          Batch
          <select className="mt-1" value={batchId} onChange={(event) => setBatchId(event.target.value)}>
            {batches.map((batch) => (
              <option key={batch.id} value={batch.id}>{batch.name}</option>
            ))}
          </select>
        </label>
        <label className="block text-[12.5px] text-text-muted">
          Subject
          <select className="mt-1" value={subjectId} onChange={(event) => setSubjectId(event.target.value)}>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>{subject.name}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="overflow-hidden rounded-xl border border-border bg-surface">
        <table className="w-full border-collapse text-[13.5px]">
          <thead>
            <tr>
              {["Student", "Present", "Late", "Absent"].map((header) => (
                <th key={header} className="border-b border-border px-2.5 py-2 text-left text-xs font-medium text-text-faint">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((student) => (
              <tr key={student.studentId}>
                <td className="border-b border-border px-2.5 py-3">{student.name}</td>
                {OPTIONS.map((option) => (
                  <td key={option} className="border-b border-border px-2.5 py-3">
                    <input
                      type="radio"
                      name={student.studentId}
                      checked={marks[student.studentId] === option}
                      onChange={() => setMarks((current) => ({ ...current, [student.studentId]: option }))}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {error && <p className="mt-3 text-[12.5px] text-danger">{error}</p>}
      {saved && <p className="mt-3 text-[12.5px] text-accent">Attendance saved.</p>}
      <Button variant="primary" className="mt-4" disabled={saving || rows.length === 0} onClick={submit}>
        {saving ? "Saving…" : "Save attendance"}
      </Button>
    </div>
  );
}
