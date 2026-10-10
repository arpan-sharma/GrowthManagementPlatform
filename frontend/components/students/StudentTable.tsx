"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { attendanceZone, trend } from "@/lib/rules";
import type { FeeStatus, Student, StudentRecord } from "@/lib/types";
import { DataTable, Td } from "../ui/DataTable";
import { Tag } from "../ui/Tag";

const FEE_TONE: Record<FeeStatus, "good" | "warn" | "bad"> = {
  Paid: "good",
  Partial: "warn",
  Overdue: "bad",
};

const TREND_LABEL = {
  Improving: "↑ Improving",
  Dropping: "↓ Dropping",
  Steady: "→ Steady",
};

const ZONE_LABEL = {
  bad: "Danger",
  warn: "Alert",
  good: "Good",
} as const;

const ZONE_LOOK = {
  bad: "bg-[#e11d48] text-white",
  warn: "bg-[#f59e0b] text-[#1a1a18]",
  good: "bg-[#16a34a] text-white",
} as const;

export function StudentTable({
  students,
  records = [],
}: {
  students: Student[];
  records?: StudentRecord[];
}) {
  const router = useRouter();
  const [batchQuery, setBatchQuery] = useState("");
  const [nameQuery, setNameQuery] = useState("");
  const previous = useMemo(
    () => Object.fromEntries(records.map((record) => [record.id, record.previousOverallAverage])),
    [records],
  );

  const rows = students.filter((student) => {
    const batchLabel = (student.batchName || student.batchId).toLowerCase();
    const batch = batchLabel.includes(batchQuery.trim().toLowerCase());
    const name = student.name.toLowerCase().includes(nameQuery.trim().toLowerCase());
    return batch && name;
  });

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2.5">
        <input
          value={batchQuery}
          onChange={(event) => setBatchQuery(event.target.value)}
          placeholder="Search by batch"
          className="min-w-[160px] flex-1"
        />
        <input
          value={nameQuery}
          onChange={(event) => setNameQuery(event.target.value)}
          placeholder="Search by student name"
          className="min-w-[160px] flex-1"
        />
      </div>
      <DataTable headers={["Name", "Batch", "Today", "Attendance", "Trend", "Fees", "Flag"]}>
        {rows.map((student) => {
          const studentTrend = trend(student.overallAverage, previous[student.id] ?? null);
          const zone = attendanceZone(student.attendancePct);
          return (
            <tr
              key={student.id}
              className="cursor-pointer hover:bg-surface-muted"
              onClick={() => router.push(`/dashboard/students/${student.id}`)}
            >
              <Td>{student.name}</Td>
              <Td>{student.batchName || student.batchId}</Td>
              <Td>{student.today ?? "—"}</Td>
              <Td>{student.attendancePct === null ? "—" : `${student.attendancePct}%`}</Td>
              <Td>{studentTrend ? TREND_LABEL[studentTrend] : "—"}</Td>
              <Td>{student.feeStatus ? <Tag tone={FEE_TONE[student.feeStatus]}>{student.feeStatus}</Tag> : "—"}</Td>
              <Td>
                {zone ? (
                  <span className={`inline-block rounded-full px-2 py-0.5 text-[11.5px] font-medium ${ZONE_LOOK[zone]}`}>
                    {ZONE_LABEL[zone]}
                  </span>
                ) : (
                  "—"
                )}
              </Td>
            </tr>
          );
        })}
      </DataTable>
      {rows.length === 0 && <p className="mt-3 text-[13px] text-text-muted">No students match.</p>}
    </div>
  );
}
