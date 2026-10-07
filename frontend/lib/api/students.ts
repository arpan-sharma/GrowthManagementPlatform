import type { Student, StudentRecord } from "@/lib/types";

type ApiStudent = {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  contact_number: string;
  batch_id: string;
  batch_name: string;
  is_active: boolean;
  today: "Present" | "Late" | "Absent" | null;
  attendance_pct: number | null;
};

export async function fetchStudents(): Promise<{ students: Student[]; records: StudentRecord[] }> {
  const response = await fetch("/backend/students");
  if (!response.ok) {
    throw new Error("Could not load students.");
  }
  const rows = (await response.json()) as ApiStudent[];
  const students = rows.map(toStudent);
  const records = rows.map(toRecord);
  return { students, records };
}

function toStudent(row: ApiStudent): Student {
  return {
    id: row.id,
    name: `${row.first_name} ${row.last_name}`.trim(),
    batchId: row.batch_name,
    parentPhone: "",
    attendancePct: row.attendance_pct,
    overallAverage: null,
    feeStatus: null,
    flagged: false,
    today: row.today,
  };
}

function toRecord(row: ApiStudent): StudentRecord {
  return {
    id: row.id,
    name: `${row.first_name} ${row.last_name}`.trim(),
    batchId: row.batch_name,
    parentPhone: "",
    attendancePct: 0,
    overallAverage: null,
    previousOverallAverage: null,
    today: null,
  };
}
