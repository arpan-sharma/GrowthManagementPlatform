"use client";

import { createContext, useContext } from "react";
import type { Batch, Chapter, FeeRecord, Notice, Student, StudentRecord, SubjectScore, Test } from "@/lib/types";

export type TeacherSnapshot = {
  records: StudentRecord[];
  subjects: Record<string, SubjectScore[]>;
  chapters: Record<string, Chapter[]>;
  fees: FeeRecord[];
  tests: Test[];
  notices: Notice[];
  batches: { id: string; name: string }[];
};

export type TeacherData = TeacherSnapshot & {
  students: Student[];
  batchList: Batch[];
  addStudent: (input: { name: string; batchId: string; parentPhone: string; parentEmail?: string }) => void;
  saveAttendance: (marks: Record<string, StudentRecord["today"]>) => void;
  markPaid: (studentId: string) => void;
  addTest: (test: Test) => void;
  addNotice: (notice: Notice) => void;
};

export const TeacherContext = createContext<TeacherData | null>(null);

export function useTeacherData(): TeacherData {
  const value = useContext(TeacherContext);
  if (!value) throw new Error("Teacher data is only available on teacher pages.");
  return value;
}
