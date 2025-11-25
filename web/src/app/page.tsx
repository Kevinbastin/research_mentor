"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Sidebar } from "@/components/Sidebar";
import { Notebook } from "@/components/Notebook";
import { MentorChat } from "@/components/MentorChat";
import { PenTool, Layout, Sparkles } from "lucide-react";

// Dynamically import Tldraw with SSR disabled to prevent duplicate instance errors
const Whiteboard = dynamic(() => import("@/components/Whiteboard").then(mod => mod.Whiteboard), { 
  ssr: false,
  loading: () => <div className="flex h-full w-full items-center justify-center text-stone-400">Loading Canvas...</div>
});

export default function Home() {
  const [view, setView] = useState<'notebook' | 'whiteboard'>('notebook');
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-stone-50">
       <Sidebar />
       
       <div className="flex-1 flex flex-col relative min-w-0">
          {/* View Switcher & Toolbar */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-stone-200 bg-white">
             <div className="flex items-center gap-1 p-1 bg-stone-100 rounded-lg border border-stone-200">
                <button 
                    onClick={() => setView('notebook')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${view === 'notebook' ? 'bg-white text-stone-800 shadow-sm ring-1 ring-stone-200' : 'text-stone-500 hover:text-stone-700'}`}
                >
                    <PenTool size={14} />
                    Write
                </button>
                <button 
                    onClick={() => setView('whiteboard')}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${view === 'whiteboard' ? 'bg-white text-stone-800 shadow-sm ring-1 ring-stone-200' : 'text-stone-500 hover:text-stone-700'}`}
                >
                    <Layout size={14} />
                    Canvas
                </button>
             </div>

             <div className="flex items-center gap-2">
                <button 
                    onClick={() => setIsChatOpen(!isChatOpen)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all shadow-sm border ${
                        isChatOpen 
                        ? 'bg-stone-100 border-stone-200 text-stone-800' 
                        : 'bg-stone-900 border-transparent text-white hover:bg-stone-800'
                    }`}
                >
                    <Sparkles size={14} className="text-yellow-400" />
                    {isChatOpen ? 'Close Mentor' : 'Ask Mentor'}
                </button>
             </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 relative overflow-hidden bg-stone-50/50">
             {view === 'notebook' ? (
                 <div className="h-full overflow-y-auto">
                     <Notebook />
                 </div>
             ) : (
                 <div className="h-full w-full bg-white">
                     <Whiteboard />
                 </div>
             )}
             
             {/* Floating Mentor Chat Overlay */}
             <MentorChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
          </div>
       </div>
    </main>
  );
}
