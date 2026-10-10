import type { FeeStatus, ScoreLevel, SubjectScore, Trend } from "./types";

export const APP_TODAY = "2026-09-26";
export const ATTENDANCE_FLAG_BELOW = 80;
export const ATTENDANCE_RED_BELOW = 50;
export const TREND_DELTA = 2;
export const PASS_MARK_PCT = 40;
export const TOPIC_GOOD_AT = 75;
export const TOPIC_AVERAGE_AT = 50;
export const TOPIC_MIN_ATTEMPTS = 5;

export function feeStatus(balance: number, dueDate: string, today: string): FeeStatus {
  if (balance === 0) return "Paid";
  if (dueDate < today) return "Overdue";
  return "Partial";
}

export function trend(latest: number | null, previous: number | null): Trend | null {
  if (latest === null || previous === null) return null;
  const delta = latest - previous;
  if (delta >= TREND_DELTA) return "Improving";
  if (delta <= -TREND_DELTA) return "Dropping";
  return "Steady";
}

export function droppedThreeInARow(scores: number[]): boolean {
  if (scores.length < 3) return false;
  const last3 = scores.slice(-3);
  return last3[1] < last3[0] && last3[2] < last3[1];
}

export function attendanceZone(attendancePct: number | null): "good" | "warn" | "bad" | null {
  if (attendancePct === null) return null;
  if (attendancePct < ATTENDANCE_RED_BELOW) return "bad";
  if (attendancePct <= ATTENDANCE_FLAG_BELOW) return "warn";
  return "good";
}

export function flagReason(attendancePct: number, subjects: SubjectScore[]): string | undefined {
  const reasons: string[] = [];

  for (const subject of subjects) {
    if (!droppedThreeInARow(subject.last4Scores)) continue;
    const last3 = subject.last4Scores.slice(-3);
    reasons.push(
      `${subject.subject} score dropped 3 tests in a row (${last3.join(" → ")})`,
    );
  }

  if (attendancePct <= ATTENDANCE_FLAG_BELOW) {
    reasons.push(`Attendance ${attendancePct}%`);
  }

  return reasons.length > 0 ? reasons.join(". ") : undefined;
}

export function scoreLevel(scorePct: number): Exclude<ScoreLevel, "Not enough data"> {
  if (scorePct >= TOPIC_GOOD_AT) return "Good";
  if (scorePct >= TOPIC_AVERAGE_AT) return "Average";
  return "Needs improvement";
}

export function topicLevel(scorePct: number, attempted: number): ScoreLevel {
  if (attempted < TOPIC_MIN_ATTEMPTS) return "Not enough data";
  return scoreLevel(scorePct);
}
