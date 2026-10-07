"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { StudentTable } from "@/components/students/StudentTable";
import { buttonClass } from "@/components/ui/Button";
import { fetchStudents } from "@/lib/api/students";
import type { Student, StudentRecord } from "@/lib/types";

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [records, setRecords] = useState<StudentRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudents()
      .then((result) => {
        setStudents(result.students);
        setRecords(result.records);
      })
      .catch(() => setError("Could not load students from the API."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2.5">
        <h1 className="m-0 text-[21px] font-semibold">Students</h1>
        <Link href="/dashboard/students/new" className={buttonClass("primary")}>
          + Add student
        </Link>
      </div>
      {loading && <p className="text-[13px] text-text-muted">Loading students…</p>}
      {error && <p className="text-[13px] text-danger">{error}</p>}
      {!loading && !error && <StudentTable students={students} records={records} />}
    </div>
  );
}
