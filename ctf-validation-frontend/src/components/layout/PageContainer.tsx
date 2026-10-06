import type { ReactNode } from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";

export default function PageContainer({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="shell">
      <Sidebar />
      <main>
        <Header title={title} />
        <section className="content">{children}</section>
      </main>
    </div>
  );
}
