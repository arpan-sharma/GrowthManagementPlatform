import { authHeaders } from "./auth";

import type { Chapter, FeeRecord, Notice, Question, Student, SubjectScore, Test, TodayStatus } from "./types";



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

  previous_overall_average?: number | null;

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

type ApiNotice = { id: string; title: string; content: string; date: string | null; status: string };
type ApiTest = { id: string; name: string; subject_id: string; subject_name: string; chapter_id: string; chapter_name: string; batch_id: string | null; on_date: string; max_marks: number; status: string; batch_average: number | null; questions: ApiQuestion[] };
type ApiQuestion = { id: string; text: string; question_type: string; marks: number; chapter_id: string; topic_id: string; answer?: string };

export type ApiDashboard = { batch_count: number; student_count: number; present_today: number; absent_today: number; attendance_pct: number; flagged: ApiStudent[]; notices: ApiNotice[] };
export type ApiBatch = { id: string; name: string; start_date?: string; end_date?: string; status: string; student_count: number };
export type ApiSubject = { id: string; name: string; description: string };
export type ApiChapterResource = { id: string; subject_id: string; name: string };
export type ApiTopicResource = { id: string; chapter_id: string; name: string };



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

  if (response.status === 401 && typeof window !== "undefined") {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("auth_user");
    window.location.href = "/login";
  }

  const responseText = await response.text();
  let data: any = {};
  try {
    data = responseText ? JSON.parse(responseText) : {};
  } catch {
    data = {};
  }

  if (!response.ok) {
    const details = Array.isArray(data?.error?.details)
      ? data.error.details
          .map((item: { field?: string; message?: string }) => {
            const label = item.field ? `${item.field.replaceAll("_", " ")}: ` : "";
            return item.message ? `${label}${item.message}` : "";
          })
          .filter(Boolean)
          .join(" ")
      : "";
    const detail = typeof data?.detail === "string"
      ? data.detail
      : Array.isArray(data?.detail)
        ? data.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(" ")
        : "";
    throw new Error(details || data?.error?.message || detail || `Request failed (${response.status}).`);
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

    batchName: row.batch_name || row.batch_id,

    parentPhone: row.contact_number,

    parentEmail: row.email ?? undefined,

    attendancePct: row.attendance_pct,

    overallAverage: row.overall_average,

    previousOverallAverage: row.previous_overall_average,

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

function toNotice(row: ApiNotice): Notice {
  return { id: row.id, text: row.content || row.title, postedAt: row.date ?? "", batchId: "All" };
}

function toTest(row: ApiTest): Test {
  const questions: Question[] = row.questions.map((question) => ({
    id: question.id,
    text: question.text,
    type: question.question_type === "MCQ" ? "MCQ" : question.question_type === "Numerical" ? "Numerical" : "Short answer",
    marks: question.marks,
    chapterId: question.chapter_id,
    topicId: question.topic_id,
    answer: question.answer,
  }));
  return {
    id: row.id, subject: row.subject_name, chapterId: row.chapter_id, chapterName: row.chapter_name,
    batchId: row.batch_id ?? "All", date: row.on_date, maxMarks: row.max_marks,
    status: row.status === "Done" || row.status === "done" ? "Done" : row.status === "Marks pending" || row.status === "marks_pending" ? "Marks pending" : "Upcoming",
    batchAverage: row.batch_average ?? undefined, questions,
  };
}

export async function fetchDashboard(): Promise<ApiDashboard> {
  const dashboard = await apiFetch<Omit<ApiDashboard, "attendance_pct"> & { attendance_pct?: number | null }>("/dashboard");
  if (typeof dashboard.attendance_pct === "number" && Number.isFinite(dashboard.attendance_pct)) {
    return dashboard as ApiDashboard;
  }

  // Older backend instances do not return the dashboard aggregate yet.
  // Use the live student resource as a fallback instead of rendering a false 0%.
  const students = await fetchStudents();
  const attendancePct = students.length
    ? Math.round(students.reduce((total, student) => total + student.attendancePct, 0) / students.length)
    : 0;
  return { ...dashboard, attendance_pct: attendancePct };
}

export type ApiCurrentUser = { id: string; first_name: string; last_name: string; email?: string | null; role: string };
export async function fetchCurrentUser(): Promise<ApiCurrentUser> {
  return apiFetch<ApiCurrentUser>("/auth/me");
}

export async function fetchNotices(): Promise<Notice[]> {
  return (await apiFetch<ApiNotice[]>("/notices")).map(toNotice);
}

export async function createNotice(input: { title: string; content: string; date?: string }): Promise<Notice> {
  return toNotice(await apiFetch<ApiNotice>("/notices", { method: "POST", body: JSON.stringify(input) }));
}

export async function fetchTests(): Promise<Test[]> {
  return (await apiFetch<ApiTest[]>("/tests")).map(toTest);
}

export type CreateTestInput = { name: string; subjectId: string; chapterId: string; batchId: string; date: string; maxMarks: number };
export async function createTest(input: CreateTestInput): Promise<Test> {
  const row = await apiFetch<ApiTest>("/tests", { method: "POST", body: JSON.stringify({
    name: input.name, subject_id: input.subjectId, chapter_id: input.chapterId,
    batch_id: input.batchId, on_date: input.date, max_marks: input.maxMarks,
  }) });
  return toTest(row);
}

export async function createTestQuestion(testId: string, input: { text: string; questionType: "MCQ" | "Short answer"; marks: number; chapterId: string; topicId: string; answer?: string }): Promise<void> {
  await apiFetch(`/tests/${testId}/questions`, { method: "POST", body: JSON.stringify({
    text: input.text, question_type: input.questionType, marks: input.marks,
    chapter_id: input.chapterId, topic_id: input.topicId, answer: input.answer ?? "",
  }) });
}

export async function fetchFees(): Promise<ApiFee[]> {
  return apiFetch<ApiFee[]>("/fees");
}

export async function setFeePlan(studentId: string, total: number, dueDate: string): Promise<ApiFee> {
  return apiFetch<ApiFee>(`/fees/${studentId}`, { method: "PUT", body: JSON.stringify({ total, due_date: dueDate }) });
}

export async function recordFeePayment(studentId: string, amount: number): Promise<ApiFee> {
  return apiFetch<ApiFee>(`/fees/${studentId}/payments`, { method: "POST", body: JSON.stringify({ amount }) });
}

export async function fetchChapters(subjectId: string): Promise<ApiChapterResource[]> {
  return apiFetch<ApiChapterResource[]>(`/chapters?${new URLSearchParams({ subject_id: subjectId })}`);
}

export async function fetchTopics(chapterId: string): Promise<ApiTopicResource[]> {
  return apiFetch<ApiTopicResource[]>(`/topics?${new URLSearchParams({ chapter_id: chapterId })}`);
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



export async function fetchStudents(): Promise<Student[]> {
  const rows = await apiFetch<ApiStudent[]>("/students");
  return rows.map(toStudent);
}

export type CreateStudentInput = {
  firstName: string;
  lastName: string;
  email: string;
  contactNumber: string;
  rollNumber: string;
  batchId: string;
  password: string;
};

function normalizePhone(value: string) {
  const trimmed = value.trim();
  const plus = trimmed.startsWith("+") ? "+" : "";
  return plus + trimmed.replace(/[^\d]/g, "");
}

export async function createStudent(input: CreateStudentInput): Promise<Student> {
  const row = await apiFetch<ApiStudent>("/students", {
    method: "POST",
    body: JSON.stringify({
      first_name: input.firstName,
      last_name: input.lastName,
      email: input.email,
      contact_number: normalizePhone(input.contactNumber),
      roll_number: input.rollNumber,
      batch_id: input.batchId,
      password: input.password,
    }),
  });
  return toStudent(row);
}

export async function fetchBatches() {

  return apiFetch<{ id: string; name: string; start_date?: string; end_date?: string; status: string; student_count: number }[]>(

    "/batches",

  );

}



export async function fetchSubjects() {

  return apiFetch<{ id: string; name: string; description: string }[]>("/subjects");

}
