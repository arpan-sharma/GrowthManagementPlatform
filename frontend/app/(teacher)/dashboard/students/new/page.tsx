"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createStudent, fetchBatches } from "@/lib/api";

export default function AddStudentPage() {
  const router = useRouter();
  const [batches, setBatches] = useState<{ id: string; name: string }[]>([]);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [batchId, setBatchId] = useState("");
  const [contactNumber, setContactNumber] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [loadingBatches, setLoadingBatches] = useState(true);

  useEffect(() => {
    let active = true;
    fetchBatches()
      .then((rows) => {
        if (!active) return;
        setBatches(rows);
        setBatchId((current) => current || rows[0]?.id || "");
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Could not load batches.");
      })
      .finally(() => {
        if (active) setLoadingBatches(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function submit() {
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !batchId || !contactNumber.trim() || !rollNumber.trim() || !password) {
      setError("Fill in all required fields.");
      return;
    }
    const phone = contactNumber.trim().replace(/[^\d+]/g, "");
    if (!/^\+?[0-9]{10,15}$/.test(phone)) {
      setError("Contact number must be 10–15 digits, optional + at the start. Example: 9876543210");
      return;
    }
    if (!/^(?=.*[A-Za-z])(?=.*\d).{8,}$/.test(password)) {
      setError("Password must be at least 8 characters and include a letter and a number.");
      return;
    }
    setPending(true);
    setError("");
    try {
      await createStudent({
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        contactNumber: contactNumber.trim(),
        rollNumber: rollNumber.trim(),
        batchId,
        password,
      });
      router.push("/dashboard/students");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add student.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <Link href="/dashboard/students" className={`${buttonClass()} mb-4`}>
        ← Back
      </Link>
      <h1 className="m-0 mb-4 text-[21px] font-semibold">Add student</h1>
      <Card>
        <div className="grid gap-3.5 sm:grid-cols-2">
          <label className="block text-[12.5px] text-text-muted">
            First name
            <input className="mt-1" value={firstName} placeholder="Ananya" onChange={(event) => setFirstName(event.target.value)} />
          </label>
          <label className="block text-[12.5px] text-text-muted">
            Last name
            <input className="mt-1" value={lastName} placeholder="Rao" onChange={(event) => setLastName(event.target.value)} />
          </label>
          <label className="block text-[12.5px] text-text-muted">
            Email
            <input className="mt-1" type="email" value={email} placeholder="parent@email.com" onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="block text-[12.5px] text-text-muted">
            Contact number
            <input className="mt-1" value={contactNumber} placeholder="9876543210" inputMode="tel" onChange={(event) => setContactNumber(event.target.value)} />
            <span className="mt-1 block text-[11px] text-text-faint">10–15 digits only, optional + (no spaces)</span>
          </label>
          <label className="block text-[12.5px] text-text-muted">
            Roll number
            <input className="mt-1" value={rollNumber} placeholder="S010" onChange={(event) => setRollNumber(event.target.value)} />
          </label>
          <label className="block text-[12.5px] text-text-muted">
            Batch
            <select className="mt-1" value={batchId} disabled={loadingBatches} onChange={(event) => setBatchId(event.target.value)}>
              {batches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  {batch.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-[12.5px] text-text-muted sm:col-span-2">
            Temporary password
            <input className="mt-1" type="password" value={password} placeholder="At least 8 characters, letter and number" onChange={(event) => setPassword(event.target.value)} />
          </label>
        </div>
        {error && <p className="mb-0 mt-3 text-[12.5px] text-danger">{error}</p>}
      </Card>
      <Button variant="primary" className="mt-4" disabled={pending || loadingBatches} onClick={submit}>
        {pending ? "Adding…" : "Add student"}
      </Button>
    </div>
  );
}
