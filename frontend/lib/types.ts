export interface Batch {
  id: string;
  name: string;
  studentCount: number;
}

export interface Student {
  id: string;
  name: string;
  batchId: string;
  batchName?: string;
  parentPhone: string;
  parentEmail?: string;
  attendancePct: number | null;
  overallAverage: number | null;
  previousOverallAverage?: number | null;
  feeStatus: "Paid" | "Partial" | "Overdue" | null;
  flagged: boolean;
  flagReason?: string;
  today: "Present" | "Late" | "Absent" | null;
}

export interface SubjectScore {
  subject: "Maths" | "Chemistry" | "Physics";
  latestScore: number;
  last4Scores: number[];
  batchAverageDiff: number;
  subjectAttendancePct: number;
}

export interface Topic {
  id: string;
  name: string;
  chapterId: string;
  scorePct: number;
  attempted: number;
}

export interface Chapter {
  id: string;
  name: string;
  subject: string;
  scorePct: number;
  topics: Topic[];
}

export interface Question {
  id: string;
  text: string;
  type: "MCQ" | "Short answer" | "Numerical";
  marks: number;
  chapterId: string;
  topicId: string;
  answer?: string;
}

export interface Test {
  id: string;
  subject: string;
  chapterId: string;
  chapterName: string;
  batchId: string | "All";
  date: string;
  maxMarks: number;
  status: "Upcoming" | "Marks pending" | "Done";
  batchAverage?: number;
  questions: Question[];
}

export interface FeeRecord {
  studentId: string;
  paid: number;
  balance: number;
  dueDate: string;
  status: "Paid" | "Partial" | "Overdue";
}

export interface Notice {
  id: string;
  text: string;
  postedAt: string;
  batchId: string | "All";
}

export type TodayStatus = "Present" | "Late" | "Absent";
export type FeeStatus = "Paid" | "Partial" | "Overdue";
export type Trend = "Improving" | "Dropping" | "Steady";
export type ScoreLevel = "Good" | "Average" | "Needs improvement" | "Not enough data";

export interface StudentRecord {
  id: string;
  name: string;
  batchId: string;
  parentPhone: string;
  parentEmail?: string;
  attendancePct: number;
  overallAverage: number | null;
  previousOverallAverage: number | null;
  today: TodayStatus | null;
}
