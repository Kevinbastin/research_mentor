import { Plus, Search, BookOpen, Map } from 'lucide-react';

export const TheDock = () => {
  return (
    <div className="absolute bottom-8 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-2xl border border-slate-800 bg-slate-950/80 p-2 shadow-2xl backdrop-blur-xl">
      <DockButton icon={<Plus size={20} />} label="New Thread" active />
      <div className="h-4 w-px bg-slate-800" />
      <DockButton icon={<Search size={20} />} label="Search" />
      <DockButton icon={<BookOpen size={20} />} label="Library" />
      <div className="h-4 w-px bg-slate-800" />
      <DockButton icon={<Map size={20} />} label="Minimap" />
    </div>
  );
};

const DockButton = ({ icon, label, active }: { icon: React.ReactNode, label: string, active?: boolean }) => (
  <button
    className={`
      group relative flex h-10 w-10 items-center justify-center rounded-xl transition-all
      ${active ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'}
    `}
    title={label}
  >
    {icon}
  </button>
);
