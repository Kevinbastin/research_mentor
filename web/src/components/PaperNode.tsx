import { memo } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import { FileText, Users, Calendar, Quote } from 'lucide-react';

type PaperNodeData = Node<{
  title: string;
  authors: string;
  year: string;
  citations: number;
  abstract: string;
}>;

const PaperNode = ({ data, isConnectable }: NodeProps<PaperNodeData>) => {
  return (
    <div className="group relative flex w-[350px] flex-col overflow-hidden rounded-lg border border-stone-800 bg-[#1c1c1e] shadow-2xl transition-all hover:border-stone-600">
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        className="!h-3 !w-3 !bg-stone-600 transition-colors group-hover:!bg-orange-500"
      />
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
        className="!h-3 !w-3 !bg-stone-600 transition-colors group-hover:!bg-orange-500"
      />

      {/* Header - Title & Meta */}
      <div className="border-b border-stone-800 bg-[#242426] p-4 relative">
        {/* Window Controls */}
         <div className="absolute right-3 top-3 flex gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
            <div className="h-2.5 w-2.5 rounded-full bg-stone-700 hover:bg-yellow-600/80 transition-colors cursor-pointer" />
            <div className="h-2.5 w-2.5 rounded-full bg-stone-700 hover:bg-red-600/80 transition-colors cursor-pointer" />
        </div>

        <div className="mb-2 flex items-start justify-between gap-2">
            <div className="rounded bg-stone-800 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-stone-400">
              PDF
            </div>
             <FileText size={14} className="text-stone-500" />
        </div>
        <h3 className="font-serif text-lg font-medium leading-snug text-stone-200">
          {data.title}
        </h3>
        
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-stone-500">
          <div className="flex items-center gap-1.5">
            <Users size={12} />
            <span className="max-w-[120px] truncate">{data.authors}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar size={12} />
            <span>{data.year}</span>
          </div>
           <div className="flex items-center gap-1.5 text-stone-400">
            <Quote size={12} />
            <span>{data.citations}</span>
          </div>
        </div>
      </div>

      {/* Abstract Snippet */}
      <div className="bg-[#1c1c1e] p-4">
        <p className="line-clamp-4 text-xs leading-relaxed text-stone-400">
          {data.abstract}
        </p>
      </div>
      
      {/* Action Bar */}
      <div className="flex items-center justify-between border-t border-stone-800 bg-[#18181a] px-4 py-2">
         <button className="text-[10px] font-medium text-stone-500 hover:text-stone-300">
            Read Full Paper →
         </button>
      </div>
    </div>
  );
};

export default memo(PaperNode);
