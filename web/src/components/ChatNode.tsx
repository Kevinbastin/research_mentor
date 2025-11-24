import { memo } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import { MessageSquare, Bot } from 'lucide-react';

type ChatNodeData = Node<{
  prompt: string;
  response: string;
}>;

const ChatNode = ({ data, isConnectable }: NodeProps<ChatNodeData>) => {
  return (
    <div className="group relative flex w-[400px] flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900/90 shadow-xl backdrop-blur-md transition-all hover:border-slate-700">
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={isConnectable}
        className="!h-3 !w-3 !bg-slate-500 transition-colors group-hover:!bg-blue-500"
      />

      {/* User Prompt Section */}
      <div className="flex gap-3 border-b border-slate-800 bg-slate-900/50 p-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-800 text-slate-400">
          <MessageSquare size={14} />
        </div>
        <div className="text-sm leading-relaxed text-slate-300">
          {data.prompt}
        </div>
      </div>

      {/* AI Response Section */}
      <div className="flex gap-3 bg-gradient-to-b from-slate-900/50 to-slate-900/20 p-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400">
          <Bot size={16} />
        </div>
        <div className="prose prose-invert prose-sm max-w-none text-slate-300">
          {data.response}
        </div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={isConnectable}
        className="!h-3 !w-3 !bg-slate-500 transition-colors group-hover:!bg-blue-500"
      />
    </div>
  );
};

export default memo(ChatNode);
