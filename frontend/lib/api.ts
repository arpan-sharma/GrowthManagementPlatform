import { authHeaders } from "./auth";
import type { Chapter, FeeRecord, Student, SubjectScore, TodayStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ROOT = `${API_BASE}/api/v1/institutions`;

type ApiStudent = {
  id: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  contact_number: string;
  batch_id: string;
  batch_name?: string;
  roll_number: string;
  is_active?: boolean;
  attendance_pct: number;
  overall_average: number | null;
  previous_overall_average: number | null;
  fee_status: Student["feeStatus"];
  flagged: boolean;
  flag_reason?: string | null;
  today: TodayStatus | null;
};

type ApiSubjectScore = {
  subject: string;
  latest_score: number;
  last_4_scores: number[];
  batch_average_diff: number;
  subject_attendance_pct: number;
};

type ApiTopic = {
  id: string;
  name: string;
  chapter_id: string;
  score_pct: number;
  attempted: number;
};

type ApiChapter = {
  id: string;
  name: string;
  subject: string;
  score_pct: number;
  topics: ApiTopic[];
};

type ApiFee = {
  student_id: string;
  total: number;
  paid: number;
  balance: number;
  due_date: string;
  status: FeeRecord["status"];
};

export type StudentProfile = {
  student: Student;
  subjects: SubjectScore[];
  chapters: Chapter[];
  fee: FeeRecord | null;
};

export type AttendanceSession = {
  batchId: string;
  batchName: string;
  subjectId: string;
  subjectName: string;
  onDate: string;
  students: { studentId: string; name: string; rollNumber: string; status: TodayStatus | null }[];
};

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${ROOT}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
    credentials: "include",
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.error?.message ?? "Request failed.");
  }
  return data as T;
}

function fullName(first: string, last: string) {
  return `${first} ${last}`.trim();
}

function toStudent(row: ApiStudent): Student {
  return {
    id: row.id,
    name: fullName(row.first_name, row.last_name),
    batchId: row.batch_id,
    parentPhone: row.contact_number,
    parentEmail: row.email ?? undefined,
    attendancePct: row.attendance_pct,
    overallAverage: row.overall_average,
    feeStatus: row.fee_status,
    flagged: row.flagged,
    flagReason: row.flag_reason ?? undefined,
    today: row.today,
  };
}

function toSubjectScore(row: ApiSubjectScore): SubjectScore {
  return {
    subject: row.subject as SubjectScore["subject"],
    latestScore: row.latest_score,
    last4Scores: row.last_4_scores,
    batchAverageDiff: row.batch_average_diff,
    subjectAttendancePct: row.subject_attendance_pct,
  };
}

function toChapter(row: ApiChapter): Chapter {
  return {
    id: row.id,
    name: row.name,
    subject: row.subject,
    scorePct: row.score_pct,
    topics: row.topics.map((topic) => ({
      id: topic.id,
      name: topic.name,
      chapterId: topic.chapter_id,
      scorePct: topic.score_pct,
      attempted: topic.attempted,
    })),
  };
}

function toFee(row: ApiFee): FeeRecord {
  return {
    studentId: row.student_id,
    paid: row.paid,
    balance: row.balance,
    dueDate: row.due_date,
    status: row.status,
  };
}

export async function fetchStudentProfile(studentId: string): Promise<StudentProfile> {
  const data = await apiFetch<{
    student: ApiStudent;
    subjects: ApiSubjectScore[];
    chapters: ApiChapter[];
    fee: ApiFee | null;
  }>(`/students/${studentId}`);
  return {
    student: toStudent(data.student),
    subjects: data.subjects.map(toSubjectScore),
    chapters: data.chapters.map(toChapter),
    fee: data.fee ? toFee(data.fee) : null,
  };
}

export async function fetchAttendanceSession(batchId: string, subjectId: string, onDate?: string): Promise<AttendanceSession> {
  const query = new URLSearchParams({ batch_id: batchId, subject_id: subjectId });
  if (onDate) query.set("on_date", onDate);
  const data = await apiFetch<{
    batch_id: string;
    batch_name: string;
    subject_id: string;
    subject_name: string;
    on_date: string;
    students: {
      student_id: string;
      first_name: string;
      last_name: string;
      roll_number: string;
      status: TodayStatus | null;
    }[];
  }>(`/attendance/session?${query}`);
  return {
    batchId: data.batch_id,
    batchName: data.batch_name,
    subjectId: data.subject_id,
    subjectName: data.subject_name,
    onDate: data.on_date,
    students: data.students.map((row) => ({
      studentId: row.student_id,
      name: fullName(row.first_name, row.last_name),
      rollNumber: row.roll_number,
      status: row.status,
    })),
  };
}

export async function saveAttendanceSession(
  batchId: string,
  subjectId: string,
  marks: Record<string, TodayStatus>,
  onDate?: string,
): Promise<AttendanceSession> {
  const data = await apiFetch<{
    batch_id: string;
    batch_name: string;
    subject_id: string;
    subject_name: string;
    on_date: string;
    students: {
      student_id: string;
      first_name: string;
      last_name: string;
      roll_number: string;
      status: TodayStatus | null;
    }[];
  }>("/attendance/session", {
    method: "POST",
    body: JSON.stringify({
      batch_id: batchId,
      subject_id: subjectId,
      on_date: onDate,
      marks: Object.entries(marks).map(([student_id, status]) => ({ student_id, status })),
    }),
  });
  return {
    batchId: data.batch_id,
    batchName: data.batch_name,
    subjectId: data.subject_id,
    subjectName: data.subject_name,
    onDate: data.on_date,
    students: data.students.map((row) => ({
      studentId: row.student_id,
      name: fullName(row.first_name, row.last_name),
      rollNumber: row.roll_number,
      status: row.status,
    })),
  };
}

export async function fetchBatches() {
  return apiFetch<{ id: string; name: string; start_date?: string; end_date?: string; status: string; student_count: number }[]>(
    "/batches",
  );
}

export async function fetchSubjects() {
  return apiFetch<{ id: string; name: string; description: string }[]>("/subjects");
}
