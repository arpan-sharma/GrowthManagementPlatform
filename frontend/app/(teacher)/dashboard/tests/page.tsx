"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchTests } from "@/lib/api";
import { TestTable } from "@/components/tests/TestTable";
import { buttonClass } from "@/components/ui/Button";
import type { Test } from "@/lib/types";

export default function TestsPage() {
  const [tests, setTests] = useState<Test[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTests().then(setTests).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Could not load tests.")).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2.5">
        <h1 className="m-0 text-[21px] font-semibold">Tests</h1>
        <Link href="/dashboard/tests/create" className={buttonClass("primary")}>+ Create test</Link>
      </div>
      {loading ? <p className="text-text-muted">Loading tests…</p> : error ? <p role="alert" className="text-danger">{error}</p> : tests.length ? <TestTable tests={tests} /> : <p className="text-text-muted">No tests have been created yet.</p>}
    </div>
  );
}
