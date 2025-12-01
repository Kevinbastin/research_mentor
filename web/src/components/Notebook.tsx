import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const Notebook = () => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [pageHeight, setPageHeight] = useState(900);
  const [currentPage, setCurrentPage] = useState(1);
  const [maxPage, setMaxPage] = useState(1);
   const [mode, setMode] = useState<'paged' | 'continuous'>('paged');

  useEffect(() => {
    const computePageHeight = () => {
      // Leave room for header chrome and breathing space
      const base = Math.max(window.innerHeight - 180, 720);
      setPageHeight(base);
    };
    computePageHeight();
    window.addEventListener('resize', computePageHeight);
    return () => window.removeEventListener('resize', computePageHeight);
  }, []);
  
  useEffect(() => {
    // Re-evaluate paging when mode or height changes
    handleScroll();
  }, [mode, pageHeight]);

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Start writing your research paper... (Option+Enter for AI)',
      }),
    ],
    content: `
      <h1>Research Proposal</h1>
      <p>Start by outlining your hypothesis here.</p>
    `,
    editorProps: {
      attributes: {
        class: 'prose prose-stone prose-lg max-w-none focus:outline-none',
      },
    },
  });

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    if (mode === 'paged') {
      const page = Math.max(1, Math.floor(el.scrollTop / pageHeight) + 1);
      const total = Math.max(1, Math.ceil(el.scrollHeight / pageHeight));
      setCurrentPage(page);
      setMaxPage(total);
    } else {
      setCurrentPage(1);
      setMaxPage(1);
    }
  };

  const scrollByPage = (delta: number) => {
    if (mode !== 'paged') return;
    const el = scrollRef.current;
    if (!el) return;
    const target = Math.max(0, el.scrollTop + delta * pageHeight);
    el.scrollTo({ top: target, behavior: 'smooth' });
  };

  const pageBackground = useMemo(() => {
    if (mode !== 'paged') return undefined;
    return {
      ['--page-height' as string]: `${pageHeight}px`,
      backgroundImage:
        'linear-gradient(to bottom, transparent calc(var(--page-height) - 36px), rgba(0,0,0,0.05), transparent calc(var(--page-height) - 12px))',
      backgroundSize: '100% var(--page-height)',
    };
  }, [mode, pageHeight]);

  return (
    <div className="relative w-full h-full">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="relative h-full overflow-y-auto rounded-2xl"
        style={pageBackground}
      >
        {/* Layered page stack for book-like feel */}
        <div className="absolute inset-3 rounded-[18px] bg-white/70 shadow-[0_20px_50px_-30px_rgba(0,0,0,0.35)] -z-10" />
        <div className="absolute inset-1 rounded-[20px] bg-white/90 shadow-[0_30px_80px_-40px_rgba(0,0,0,0.35)] -z-20" />

        <div
          className="relative z-10 w-full min-h-[calc(100vh-6rem)] bg-white shadow-[0_2px_40px_-12px_rgba(0,0,0,0.08)] border border-stone-200/60 rounded-2xl overflow-hidden flex flex-col"
          style={{ minHeight: `${pageHeight}px` }}
        >
          {/* Top Accent Line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-orange-300 via-red-300 to-indigo-300 opacity-80" />

          {editor ? (
            <EditorContent 
              editor={editor} 
              className="flex-1 px-12 pt-12 pb-36 prose prose-stone prose-lg max-w-none focus:outline-none"
            />
          ) : (
            <div className="flex-1 px-12 pt-12 pb-24 text-sm text-stone-400">
              Loading editor...
            </div>
          )}
        </div>
      </div>

      {/* Page navigation & controls (viewport fixed) */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 z-50 px-3">
        <button
          onClick={() => {
            const nextMode = mode === 'paged' ? 'continuous' : 'paged';
            setMode(nextMode);
            if (nextMode === 'paged') {
              scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
            }
          }}
          className="px-3 py-1.5 rounded-full bg-white shadow-[0_4px_20px_rgba(0,0,0,0.12)] border border-stone-200 hover:translate-y-[-1px] transition-all text-[11px] font-mono text-stone-700"
        >
          {mode === 'paged' ? 'Paged view' : 'Continuous view'}
        </button>

        {mode === 'paged' && (
          <>
            <button
              onClick={() => scrollByPage(-1)}
              className="p-2 rounded-full bg-white shadow-[0_4px_20px_rgba(0,0,0,0.12)] border border-stone-200 hover:translate-y-[-1px] transition-all text-stone-600 hover:text-stone-900 disabled:opacity-40"
              title="Previous page"
              disabled={currentPage <= 1}
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => scrollByPage(1)}
              className="p-2 rounded-full bg-white shadow-[0_4px_20px_rgba(0,0,0,0.12)] border border-stone-200 hover:translate-y-[-1px] transition-all text-stone-600 hover:text-stone-900 disabled:opacity-40"
              title="Next page"
              disabled={currentPage >= maxPage}
            >
              <ChevronRight size={16} />
            </button>
            <span className="px-3 py-1 rounded-full bg-white/90 border border-stone-200 text-[11px] font-mono text-stone-600 shadow-sm">
              Page {currentPage}/{maxPage}
            </span>
          </>
        )}
      </div>
    </div>
  );
};
