"use client";

import ResearchCanvas from "@/components/ResearchCanvas";
import { Sidebar } from "@/components/Sidebar";

export default function Home() {
  return (
    <main className="flex min-h-screen overflow-hidden bg-slate-950">
       <Sidebar />
       <div className="flex-1 relative">
          <ResearchCanvas />
       </div>
    </main>
  );
}
