"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { StudentTable } from "@/components/students/StudentTable";
import { buttonClass } from "@/components/ui/Button";
import { fetchStudents } from "@/lib/api";
import type { Student } from "@/lib/types";

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    fetchStudents()
      .then((rows) => {
        if (active) setStudents(rows);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Could not load students.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
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
      {!loading && !error && <StudentTable students={students} />}
    </div>
  );
}
