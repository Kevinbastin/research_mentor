import { memo, useState } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import { MessageSquare, Bot, Send, Loader2 } from 'lucide-react';

type ChatNodeData = Node<{
  prompt: string;
  response: string;
}>;

const ChatNode = ({ data, isConnectable }: NodeProps<ChatNodeData>) => {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [prompt, setPrompt] = useState(data.prompt);
  const [response, setResponse] = useState(data.response);
  
  // If this is a new node (placeholder text), allow editing
  const isNew = prompt === "New Research Thread...";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setIsLoading(true);
    setPrompt(input); // Lock in the prompt
    setResponse("Thinking...");

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: input }),
      });
      
      if (!res.ok) throw new Error('Failed to fetch');
      
      const json = await res.json();
      setResponse(json.response);
    } catch (error) {
      setResponse("Error: Could not connect to mentor agent.");
    } finally {
      setIsLoading(false);
    }
  };

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
        
        {isNew && !isLoading ? (
          <form onSubmit={handleSubmit} className="flex w-full gap-2">
            <input
              autoFocus
              className="w-full bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none"
              placeholder="Ask a research question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button 
                type="submit" 
                disabled={!input.trim()}
                className="text-slate-500 hover:text-blue-400 disabled:opacity-50"
            >
                <Send size={14} />
            </button>
          </form>
        ) : (
          <div className="text-sm leading-relaxed text-slate-300">
            {prompt}
          </div>
        )}
      </div>

      {/* AI Response Section */}
      <div className="flex gap-3 bg-gradient-to-b from-slate-900/50 to-slate-900/20 p-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400">
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Bot size={16} />}
        </div>
        <div className="prose prose-invert prose-sm max-w-none text-slate-300">
          {response}
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
