import type { ReactNode } from "react";
import { Navbar } from "@/components/layout/Navbar";

export default function TeacherLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[960px] px-5 py-7 pb-16">{children}</main>
    </>
  );
}
