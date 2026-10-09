"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createNotice, createTest, createTestQuestion, fetchBatches, fetchChapters, fetchSubjects, fetchTopics, type ApiBatch, type ApiChapterResource, type ApiSubject, type ApiTopicResource } from "@/lib/api";

export default function CreateTestPage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<ApiSubject[]>([]);
  const [batches, setBatches] = useState<ApiBatch[]>([]);
  const [chapters, setChapters] = useState<ApiChapterResource[]>([]);
  const [topics, setTopics] = useState<ApiTopicResource[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [chapterId, setChapterId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [name, setName] = useState("");
  const [date, setDate] = useState("");
  const [maxMarks, setMaxMarks] = useState(50);
  const [addQuestion, setAddQuestion] = useState(false);
  const [questionText, setQuestionText] = useState("");
  const [questionMarks, setQuestionMarks] = useState(5);
  const [questionType, setQuestionType] = useState<"MCQ" | "Short answer">("Short answer");
  const [answer, setAnswer] = useState("");
  const [postNotice, setPostNotice] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetchSubjects(), fetchBatches()]).then(([subjectRows, batchRows]) => {
      setSubjects(subjectRows);
      setBatches(batchRows);
      setSubjectId(subjectRows[0]?.id ?? "");
      setBatchId(batchRows[0]?.id ?? "");
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load resources.")).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!subjectId) { setChapters([]); setChapterId(""); return; }
    fetchChapters(subjectId).then((rows) => { setChapters(rows); setChapterId(rows[0]?.id ?? ""); }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load chapters."));
  }, [subjectId]);

  useEffect(() => {
    if (!addQuestion || !chapterId) { setTopics([]); setTopicId(""); return; }
    fetchTopics(chapterId).then((rows) => { setTopics(rows); setTopicId(rows[0]?.id ?? ""); }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load topics."));
  }, [addQuestion, chapterId]);

  async function save() {
    setError("");
    if (!subjectId || !chapterId || !batchId || !date || !name.trim()) { setError("Select a subject, chapter, batch, test name, and date."); return; }
    if (addQuestion && (!questionText.trim() || !topicId)) { setError("Enter the question and select a topic."); return; }
    setSaving(true);
    try {
      const test = await createTest({ name: name.trim(), subjectId, chapterId, batchId, date, maxMarks });
      if (addQuestion) await createTestQuestion(test.id, { text: questionText.trim(), questionType, marks: questionMarks, chapterId, topicId, answer });
      if (postNotice) {
        const subject = subjects.find((item) => item.id === subjectId)?.name ?? "Test";
        const chapter = chapters.find((item) => item.id === chapterId)?.name ?? "";
        try { await createNotice({ title: `${subject} test`, content: `${name.trim()} — ${chapter} · ${batches.find((item) => item.id === batchId)?.name ?? batchId}`, date }); }
        catch { setError("Test was saved, but the notice could not be posted."); }
      }
      router.push("/dashboard/tests");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save test.");
    } finally { setSaving(false); }
  }

  if (loading) return <p className="text-text-muted">Loading test options…</p>;
  return (
    <div>
      <Link href="/dashboard/tests" className={`${buttonClass()} mb-4`}>← Back to tests</Link>
      <h1 className="m-0 mb-4 text-[21px] font-semibold">Create test</h1>
      <Card>
        <div className="grid gap-3.5 sm:grid-cols-2">
          <label className="text-[12.5px] text-text-muted">Test name<input className="mt-1" value={name} onChange={(e) => setName(e.target.value)} /></label>
          <label className="text-[12.5px] text-text-muted">Subject<select className="mt-1" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>{subjects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label className="text-[12.5px] text-text-muted">Batch<select className="mt-1" value={batchId} onChange={(e) => setBatchId(e.target.value)}>{batches.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label className="text-[12.5px] text-text-muted">Chapter<select className="mt-1" value={chapterId} onChange={(e) => setChapterId(e.target.value)}>{chapters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label className="text-[12.5px] text-text-muted">Date<input className="mt-1" type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label>
          <label className="text-[12.5px] text-text-muted">Maximum marks<input className="mt-1" type="number" min={1} value={maxMarks} onChange={(e) => setMaxMarks(Number(e.target.value))} /></label>
          <label className="flex items-center gap-2 text-[12.5px] text-text-muted"><input type="checkbox" checked={postNotice} onChange={(e) => setPostNotice(e.target.checked)} />Post on notice board</label>
        </div>
      </Card>
      <Card className="mt-4">
        <label className="flex items-center gap-2 text-sm font-medium"><input type="checkbox" checked={addQuestion} onChange={(e) => setAddQuestion(e.target.checked)} />Add a question</label>
        {addQuestion && <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <label className="text-[12.5px] text-text-muted sm:col-span-2">Question<textarea className="mt-1" value={questionText} onChange={(e) => setQuestionText(e.target.value)} /></label>
          <label className="text-[12.5px] text-text-muted">Topic<select className="mt-1" value={topicId} onChange={(e) => setTopicId(e.target.value)}>{topics.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label className="text-[12.5px] text-text-muted">Type<select className="mt-1" value={questionType} onChange={(e) => setQuestionType(e.target.value as "MCQ" | "Short answer")}><option value="Short answer">Short answer</option><option value="MCQ">MCQ</option></select></label>
          <label className="text-[12.5px] text-text-muted">Marks<input className="mt-1" type="number" min={1} value={questionMarks} onChange={(e) => setQuestionMarks(Number(e.target.value))} /></label>
          <label className="text-[12.5px] text-text-muted">Answer (teacher only)<input className="mt-1" value={answer} onChange={(e) => setAnswer(e.target.value)} /></label>
        </div>}
      </Card>
      {error && <p role="alert" className="mb-0 mt-3 text-[12.5px] text-danger">{error}</p>}
      <div className="mt-5 flex gap-2.5"><Button variant="primary" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save test"}</Button></div>
    </div>
  );
}
