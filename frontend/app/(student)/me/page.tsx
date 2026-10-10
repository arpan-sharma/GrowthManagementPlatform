"use client";

import { useEffect, useState } from "react";
import { ChapterTopicList } from "@/components/students/ChapterTopicList";
import { SubjectCard } from "@/components/students/SubjectCard";
import { NoticeBoard } from "@/components/dashboard/NoticeBoard";
import { StatTile } from "@/components/ui/StatTile";
import { fetchCurrentUser, fetchNotices, fetchStudentProfile, type StudentProfile } from "@/lib/api";
import { readSessionUser } from "@/lib/auth";
import type { Notice } from "@/lib/types";

export default function MyPage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const sessionUser = readSessionUser();
    const profileRequest = sessionUser
      ? fetchStudentProfile(sessionUser.id)
      : fetchCurrentUser().then((user) => fetchStudentProfile(user.id));
    Promise.all([profileRequest, fetchNotices()]).then(([studentProfile, noticeRows]) => {
      setProfile(studentProfile);
      setNotices(noticeRows);
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load your profile.")).finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-text-muted">Loading your profile…</p>;
  if (error) return <p role="alert" className="text-danger">{error}</p>;
  if (!profile) return <p>No student record is linked to this login.</p>;

  const { student, subjects, chapters } = profile;
  const subjectName = chapters[0]?.subject;
  return (
    <div>
      <h1 className="m-0 text-[22px] font-semibold">{student.name}</h1>
      <p className="mb-5 mt-1 text-[13px] text-text-muted">Batch {student.batchId}</p>
      <div className="mb-5 grid grid-cols-2 gap-3">
        <StatTile value={student.attendancePct === null ? "—" : `${student.attendancePct}%`} label="Attendance" />
        <StatTile value={student.overallAverage === null ? "—" : `${student.overallAverage}%`} label="Average" />
      </div>
      <h2 className="mb-3 text-sm font-semibold">Subjects</h2>
      {subjects.length ? <div className="grid gap-3 sm:grid-cols-3">{subjects.map((score) => <SubjectCard key={score.subject} score={score} />)}</div> : <p className="text-text-muted">No test results are available yet.</p>}
      {subjectName && <><h2 className="mb-3 mt-6 text-sm font-semibold">Chapter & topic analysis — {subjectName}</h2><ChapterTopicList chapters={chapters} /></>}
      <h2 className="mb-3 mt-6 text-sm font-semibold">Notices</h2>
      {notices.length ? <NoticeBoard notices={notices} /> : <p className="text-text-muted">There are no notices right now.</p>}
    </div>
  );
}
