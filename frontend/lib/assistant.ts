import { formatInr } from "./format";
import type { FeeRecord, Notice, Student, Test } from "./types";

export type AssistantFacts = {
  students: Student[];
  fees: FeeRecord[];
  tests: Test[];
  notices: Notice[];
};

export function replyTo(question: string, facts: AssistantFacts): string {
  const text = question.toLowerCase();
  const named = facts.students.filter((student) => text.includes(student.name.toLowerCase()));

  if (named.length === 1) return studentReply(named[0]);
  if (named.length > 1) return named.map(studentReply).join("\n\n");
  if (matches(text, ["flag", "attention", "risk"])) return flagReply(facts.students);
  if (matches(text, ["fee", "fees", "overdue", "pending", "paid"])) return feeReply(facts);
  if (matches(text, ["attendance", "absent", "present", "late"])) return attendanceReply(facts.students);
  if (matches(text, ["test", "tests", "upcoming", "exam"])) return testReply(facts.tests);
  if (matches(text, ["notice", "notices", "holiday"])) return noticeReply(facts.notices);

  return "I can answer from this class only: a student name, flags, fees, attendance, tests, or notices.";
}

function matches(text: string, words: string[]): boolean {
  return words.some((word) => text.includes(word));
}

function studentReply(student: Student): string {
  const fee = student.feeStatus ?? "no fee record";
  const flag = student.flagReason ?? "not flagged";
  const average = student.overallAverage === null ? "no average yet" : `${student.overallAverage}% average`;
  return `${student.name}, batch ${student.batchId}. Today: ${student.today ?? "not marked"}. Attendance ${student.attendancePct}%. ${average}. Fees: ${fee}. ${flag}.`;
}

function flagReply(students: Student[]): string {
  const flagged = students.filter((student) => student.flagged);
  if (flagged.length === 0) return "No students are flagged right now.";
  return flagged.map((student) => `${student.name}: ${student.flagReason}`).join("\n");
}

function feeReply(facts: AssistantFacts): string {
  const collected = facts.fees.reduce((sum, fee) => sum + fee.paid, 0);
  const pending = facts.fees.reduce((sum, fee) => sum + fee.balance, 0);
  const overdue = facts.fees.filter((fee) => fee.status === "Overdue");
  const names = overdue.map((fee) => facts.students.find((student) => student.id === fee.studentId)?.name ?? fee.studentId);
  const who = names.length === 0 ? "Nobody is overdue." : `Overdue: ${names.join(", ")}.`;
  return `Collected ${formatInr(collected)}. Pending ${formatInr(pending)}. ${who}`;
}

function attendanceReply(students: Student[]): string {
  const count = (status: Student["today"]) => students.filter((student) => student.today === status).length;
  const average = students.length === 0 ? 0 : Math.round(students.reduce((sum, student) => sum + student.attendancePct, 0) / students.length);
  return `Overall attendance is ${average}%. Today: ${count("Present")} present, ${count("Late")} late, ${count("Absent")} absent.`;
}

function testReply(tests: Test[]): string {
  if (tests.length === 0) return "No tests yet.";
  return tests.map((test) => `${test.subject} · ${test.chapterName} · ${test.status}`).join("\n");
}

function noticeReply(notices: Notice[]): string {
  if (notices.length === 0) return "No notices.";
  return notices.map((notice) => notice.text).join("\n");
}
