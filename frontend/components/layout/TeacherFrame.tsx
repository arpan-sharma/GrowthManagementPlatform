"use client";

import { useMemo, useState, type ReactNode } from "react";
import { APP_TODAY, feeStatus } from "@/lib/rules";
import { toStudent } from "@/lib/data/students";
import { Navbar } from "./Navbar";
import { TeacherContext, type TeacherData, type TeacherSnapshot } from "./teacher-context";

export type { TeacherSnapshot };
export { useTeacherData } from "./teacher-context";

export function TeacherFrame({ initial, children }: { initial: TeacherSnapshot; children: ReactNode }) {
  const [records, setRecords] = useState(initial.records);
  const [subjects] = useState(initial.subjects);
  const [chapters] = useState(initial.chapters);
  const [fees, setFees] = useState(initial.fees);
  const [tests, setTests] = useState(initial.tests);
  const [notices, setNotices] = useState(initial.notices);

  const students = useMemo(
    () =>
      records.map((record) => {
        const fee = fees.find((item) => item.studentId === record.id);
        const status = fee ? feeStatus(fee.balance, fee.dueDate, APP_TODAY) : null;
        return toStudent(record, subjects[record.id] ?? [], fee ? { ...fee, status: status ?? "Paid" } : undefined);
      }),
    [records, fees, subjects],
  );

  const batchList = useMemo(
    () =>
      initial.batches.map((batch) => ({
        ...batch,
        studentCount: records.filter((record) => record.batchId === batch.id).length,
      })),
    [initial.batches, records],
  );

  const value: TeacherData = {
    records,
    subjects,
    chapters,
    fees: fees.map((fee) => ({ ...fee, status: feeStatus(fee.balance, fee.dueDate, APP_TODAY) })),
    tests,
    notices,
    batches: initial.batches,
    students,
    batchList,
    addStudent: (input) => {
      setRecords((current) => [
        ...current,
        {
          id: `student-${Date.now()}`,
          name: input.name,
          batchId: input.batchId,
          parentPhone: input.parentPhone,
          parentEmail: input.parentEmail,
          attendancePct: 0,
          overallAverage: null,
          previousOverallAverage: null,
          today: null,
        },
      ]);
    },
    saveAttendance: (marks) => {
      setRecords((current) =>
        current.map((record) => (marks[record.id] === undefined ? record : { ...record, today: marks[record.id] })),
      );
    },
    markPaid: () => {},
    addTest: (test) => setTests((current) => [test, ...current]),
    addNotice: (notice) => setNotices((current) => [notice, ...current]),
  };

  return (
    <TeacherContext.Provider value={value}>
      <Navbar />
      <main className="mx-auto max-w-[960px] px-5 py-7 pb-16">{children}</main>
    </TeacherContext.Provider>
  );
}
