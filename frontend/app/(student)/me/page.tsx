import { ChapterTopicList } from "@/components/students/ChapterTopicList";
import { SubjectCard } from "@/components/students/SubjectCard";
import { NoticeBoard } from "@/components/dashboard/NoticeBoard";
import { StatTile } from "@/components/ui/StatTile";
import { getMyRecord } from "@/lib/data/portal";

export default async function MyPage() {
  const record = await getMyRecord();
  if (!record) return <p>No student record.</p>;

  const { student, subjects, chapters, notices } = record;
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
      <div className="grid gap-3 sm:grid-cols-3">
        {subjects.map((score) => (
          <SubjectCard key={score.subject} score={score} />
        ))}
      </div>
      {subjectName && (
        <>
          <h2 className="mb-3 mt-6 text-sm font-semibold">Chapter & topic analysis — {subjectName}</h2>
          <ChapterTopicList chapters={chapters} />
        </>
      )}
      <h2 className="mb-3 mt-6 text-sm font-semibold">Notices</h2>
      <NoticeBoard notices={notices} />
    </div>
  );
}
