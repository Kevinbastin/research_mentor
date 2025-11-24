import { useState } from 'react';
import { Book, MessageSquare, Hash, Search, GripVertical } from 'lucide-react';
import { useLibraryStore } from '@/store/useLibraryStore';

export const Sidebar = () => {
  const [activeTab, setActiveTab] = useState<'library' | 'threads'>('library');
  const { papers, threads } = useLibraryStore();

  const onDragStart = (event: React.DragEvent, type: string, data: any) => {
    event.dataTransfer.setData('application/reactflow', type);
    event.dataTransfer.setData('application/json', JSON.stringify(data));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside className="flex h-screen w-72 flex-col border-r border-white/5 bg-slate-950/80 backdrop-blur-xl">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center gap-2 text-slate-200 font-semibold mb-4">
           <div className="w-3 h-3 rounded-full bg-indigo-500" />
           Research OS
        </div>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input 
            className="w-full rounded-lg bg-slate-900/50 border border-white/5 py-2 pl-9 pr-3 text-xs text-slate-300 placeholder-slate-600 outline-none focus:border-indigo-500/30"
            placeholder="Filter files..."
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-2 pb-2 border-b border-white/5">
        <SidebarTab 
            label="Library" 
            icon={<Book size={14} />} 
            active={activeTab === 'library'} 
            onClick={() => setActiveTab('library')}
        />
        <SidebarTab 
            label="Threads" 
            icon={<MessageSquare size={14} />} 
            active={activeTab === 'threads'} 
            onClick={() => setActiveTab('threads')}
        />
      </div>

      {/* List Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {activeTab === 'library' ? (
            papers.map(paper => (
                <div 
                    key={paper.id}
                    draggable
                    onDragStart={(e) => onDragStart(e, 'paper', paper)}
                    className="group flex cursor-grab items-start gap-3 rounded-md p-2 hover:bg-slate-900/50 active:cursor-grabbing"
                >
                    <div className="mt-1 text-slate-500"><GripVertical size={14} className="opacity-0 group-hover:opacity-100" /></div>
                    <div>
                        <div className="text-sm font-medium text-slate-300 line-clamp-1">{paper.title}</div>
                        <div className="text-xs text-slate-500">{paper.authors} • {paper.year}</div>
                        <div className="mt-1 flex flex-wrap gap-1">
                            {paper.tags.map(tag => (
                                <span key={tag} className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">{tag}</span>
                            ))}
                        </div>
                    </div>
                </div>
            ))
        ) : (
            threads.map(thread => (
                <div 
                    key={thread.id}
                    draggable
                    onDragStart={(e) => onDragStart(e, 'chat', { prompt: thread.title, response: "Resumed thread..." })} // Simplified for mock
                    className="group flex cursor-grab items-start gap-3 rounded-md p-2 hover:bg-slate-900/50 active:cursor-grabbing"
                >
                     <div className="mt-1 text-slate-500"><MessageSquare size={14} /></div>
                     <div>
                        <div className="text-sm font-medium text-slate-300">{thread.title}</div>
                        <div className="text-xs text-slate-500">{thread.lastActive}</div>
                     </div>
                </div>
            ))
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-white/5 p-3 text-xs text-slate-600 flex justify-between">
         <span>4 items</span>
         <span>v0.2.0</span>
      </div>
    </aside>
  );
};

const SidebarTab = ({ label, icon, active, onClick }: any) => (
    <button 
        onClick={onClick}
        className={`
            flex flex-1 items-center justify-center gap-2 rounded-md py-1.5 text-xs font-medium transition-colors
            ${active ? 'bg-slate-800 text-slate-200' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-900/30'}
        `}
    >
        {icon}
        {label}
    </button>
);
