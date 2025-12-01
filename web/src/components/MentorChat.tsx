import { useState, useRef, useEffect } from 'react';
import { Rnd } from 'react-rnd';
import {
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ChevronRight,
  ChevronDown,
  PanelRightOpen,
  SidebarClose,
  Maximize2,
  Minimize2,
  GripHorizontal,
  ImagePlus,
  Terminal,
} from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { useChatStore, ChatAttachment } from '@/store/useChatStore';
import { useDocumentStore } from '@/store/useDocumentStore';

const ThinkingBlock = ({ content, defaultExpanded = false }: { content: string; defaultExpanded?: boolean }) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  if (!content) return null;

  return (
    <div className="mb-4 rounded-md overflow-hidden border border-stone-800 bg-[#1C1917] shadow-sm">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-1.5 bg-[#292524] hover:bg-[#44403C] transition-colors group"
      >
        <Terminal size={12} className="text-amber-500/70 group-hover:text-amber-400 transition-colors" />
        <span className="text-[10px] font-mono text-stone-400 uppercase tracking-wider font-medium">
          System_Trace
        </span>
        <div className="ml-auto flex items-center gap-2">
           <span className="text-[10px] text-stone-600 font-mono">
             {isExpanded ? 'HIDE' : 'SHOW'}
           </span>
        </div>
      </button>
      {isExpanded && (
        <div className="p-3 text-xs font-mono text-[#A8A29E] overflow-x-auto leading-relaxed border-t border-stone-800/50">
          {content}
        </div>
      )}
    </div>
  );
};

const CollapsibleMessage = ({ content }: { content: string }) => {
  return (
    <div className="text-[15px] leading-relaxed text-stone-900">
      <MarkdownRenderer content={content} />
    </div>
  );
};

const ImageAttachmentStrip = ({ attachments }: { attachments?: ChatAttachment[] }) => {
  if (!attachments || attachments.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {attachments.map((att) => (
        <div 
          key={att.id} 
          className="relative w-24 h-24 rounded-md border border-stone-200 overflow-hidden bg-stone-50 shadow-[1px_1px_0px_rgba(0,0,0,0.05)]"
        >
          <img src={att.dataUrl} alt={att.name} className="w-full h-full object-cover" />
          <div className="absolute bottom-0 left-0 right-0 bg-white/85 backdrop-blur-sm px-1 py-0.5 text-[10px] text-stone-600 truncate">
            {att.name}
          </div>
        </div>
      ))}
    </div>
  );
};

export const MentorChat = ({ 
    isOpen, 
    onClose, 
    mode, 
    onToggleMode,
    isFullscreen,
    onToggleFullscreen
}: { 
    isOpen: boolean; 
    onClose: () => void;
    mode: 'floating' | 'docked';
    onToggleMode: () => void;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
}) => {
  const [input, setInput] = useState("");
  const [pendingImages, setPendingImages] = useState<ChatAttachment[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const { 
    messages, 
    addUserMessage, 
    addAiMessage, 
    isLoading, 
    setLoading, 
    isStreaming, 
    setStreaming, 
    streamingContent, 
    streamingReasoning,
    appendContent,
    appendReasoning,
    finalizeStream,
    conversations,
    currentConversationId,
    startNewChat,
    loadConversation,
    deleteConversation,
    buildImageContext,
  } = useChatStore();
  const { getSelectedContent } = useDocumentStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent, streamingReasoning]);

  const parseResponse = (fullResponse: string): { thinking?: string, content: string } => {
    const thinkingMatch = fullResponse.match(/<thinking>([\s\S]*?)<\/thinking>/i);
    if (thinkingMatch) {
      const thinking = thinkingMatch[1].trim();
      const content = fullResponse.replace(/<thinking>[\s\S]*?<\/thinking>/i, '').trim();
      return { thinking, content };
    }
    return { content: fullResponse };
  };

  const readFileAsDataUrl = (file: File): Promise<string> => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new Error('Unable to read file'));
    reader.readAsDataURL(file);
  });

  const handleImagesSelected = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const validImages = Array.from(files).filter((file) => file.type.startsWith('image/'));
    if (validImages.length === 0) return;

    const attachments: ChatAttachment[] = [];
    for (const file of validImages) {
      try {
        const dataUrl = await readFileAsDataUrl(file);
        attachments.push({
          id: `img-${Date.now()}-${Math.random().toString(36).slice(2)}`,
          name: file.name,
          type: 'image',
          dataUrl,
          size: file.size,
          uploadedAt: Date.now(),
        });
      } catch (err) {
        console.warn('Image read failed', err);
      }
    }

    if (attachments.length) {
      setPendingImages((prev) => [...prev, ...attachments]);
    }
  };

  const removePendingImage = (id: string) => {
    setPendingImages((prev) => prev.filter((img) => img.id !== id));
  };

  const buildContentParts = (text: string, context: string, images: ChatAttachment[]) => {
    const parts: any[] = [];
    if (context) {
      parts.push({ type: 'text', text: `Context:\n${context}` });
    }
    parts.push({ type: 'text', text });
    images.forEach((img) => {
      parts.push({ 
        type: 'image_url', 
        image_url: { url: img.dataUrl } 
      });
    });
    return parts;
  };

  const stripThinkingTags = (text: string) => text.replace(/<\/?thinking>/gi, '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    const imagesForMessage = pendingImages;
    setInput("");
    setPendingImages([]);
    addUserMessage(userMsg, imagesForMessage);
    setLoading(true);

    const documentContext = getSelectedContent();
    const imageContext = buildImageContext(imagesForMessage);
    const combinedContext = [documentContext, imageContext ? `Images available this chat:\n${imageContext}` : ""]
      .filter(Boolean)
      .join("\n\n");
    const contentParts = buildContentParts(userMsg, combinedContext, imagesForMessage);

    try {
      const streamRes = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: userMsg,
          document_context: combinedContext || undefined,
          content_parts: contentParts,
        }),
      });

      if (!streamRes.ok || !streamRes.body) {
        throw new Error('Streaming unavailable');
      }

      setStreaming(true);
      setLoading(false);
      
      const reader = streamRes.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ""; 
        
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          
          try {
            const event = JSON.parse(line.slice(6));
            
            if (event.type === 'reasoning' && event.content) {
              appendReasoning(event.content);
            } else if (event.type === 'content' && event.content) {
              appendContent(stripThinkingTags(event.content));
            } else if (event.type === 'done') {
              finalizeStream();
            } else if (event.type === 'error') {
              console.error('Stream error:', event.content);
              addAiMessage(`Error: ${event.content}`);
              setStreaming(false);
            }
          } catch (parseErr) {
            console.warn('Failed to parse SSE event:', line);
          }
        }
      }
      
      finalizeStream();
      
    } catch (error) {
      console.error('Streaming failed:', error);
      try {
        const res = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: userMsg,
          document_context: combinedContext || undefined,
          content_parts: contentParts,
        }),
      });
        
        if (!res.ok) throw new Error('Failed to fetch');
        
        const json = await res.json();
        const explicitThinking = json.reasoning as string | undefined;
        const { thinking: parsedThinking, content } = parseResponse(json.response);
        const thinking = explicitThinking || parsedThinking;

        addAiMessage(content, thinking);
      } catch (fallbackError) {
        addAiMessage("Sorry, I encountered an error connecting to the backend.");
      } finally {
        setStreaming(false);
        setLoading(false);
      }
    }
  };

  if (!isOpen) return null;

  const ChatContent = (
    <div className={`
      h-full w-full bg-white flex flex-col overflow-hidden shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] border border-stone-800
      ${isMobile && mode === 'floating' ? 'fixed inset-0 z-[60] rounded-none border-0' : 'rounded-xl'}
    `}>
      {/* Header */}
      <div className={`
        flex flex-col gap-3 p-4 border-b border-stone-200 bg-stone-50/80 backdrop-blur-sm
        ${mode === 'floating' && !isMobile ? 'cursor-move drag-handle' : ''}
      `}>
        <div className="flex items-center justify-between gap-2 min-w-0">
          <div className="flex items-center gap-2.5 font-mono text-stone-900 select-none">
            <div className="bg-stone-900 p-1 rounded-sm">
              <Sparkles size={12} className="text-white" />
            </div>
            <span className="text-sm font-bold tracking-tight uppercase truncate">Research_Mentor</span>
            {mode === 'floating' && !isMobile && <GripHorizontal size={14} className="text-stone-300 ml-1" />}
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
              {mode === 'docked' && onToggleFullscreen && !isMobile && (
                 <button 
                   onClick={onToggleFullscreen}
                   className="p-1.5 text-stone-400 hover:text-stone-900 hover:bg-stone-200/50 rounded transition-colors touch-target h-auto w-auto"
                   title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                 >
                   {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                 </button>
              )}
              <button 
                onClick={onClose} 
                className="p-1.5 text-stone-400 hover:text-stone-900 hover:bg-stone-200/50 rounded transition-colors touch-target h-auto w-auto"
              >
                  <X size={18} />
              </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 min-w-0">
          <select
            className="text-xs font-mono bg-white border border-stone-200 rounded px-2 py-1 text-stone-700 focus:outline-none focus:border-stone-400 w-full sm:w-56 md:w-64 truncate"
            value={currentConversationId || ''}
            onChange={(e) => {
              if (!e.target.value) return;
              loadConversation(e.target.value);
            }}
          >
            <option value="" disabled>Select chat…</option>
            {conversations
              .slice()
              .sort((a, b) => b.updatedAt - a.updatedAt)
              .map(convo => (
                <option key={convo.id} value={convo.id}>{convo.title}</option>
              ))}
          </select>
          <button
            onClick={() => startNewChat()}
            className="px-2.5 py-1 text-[11px] font-mono rounded border border-stone-200 text-stone-600 hover:text-stone-900 hover:border-stone-400 transition-colors"
            title="New chat"
          >
            New
          </button>
          {currentConversationId && (
            <button
              onClick={() => deleteConversation(currentConversationId)}
              className="px-2 py-1 text-[11px] font-mono rounded border border-red-200 text-red-600 hover:text-white hover:bg-red-500 hover:border-red-500 transition-colors"
              title="Delete chat"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-6 bg-[#FAFAF9]" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-5 animate-slide-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`
              w-8 h-8 rounded-sm flex items-center justify-center shrink-0 border
              ${msg.role === 'ai' ? 'bg-white border-stone-800 text-stone-900 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' : 'bg-stone-900 border-stone-900 text-white'}
            `}>
              {msg.role === 'ai' ? <Bot size={16} /> : <User size={16} />}
            </div>
            <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {msg.role === 'ai' && msg.thinking && (
                  <ThinkingBlock content={msg.thinking} defaultExpanded={idx === messages.length - 1} />
                )}
                <div className={`
                  rounded-lg px-5 py-3.5 min-w-0 text-[15px] leading-relaxed border
                  ${msg.role === 'ai' 
                    ? 'bg-white border-stone-200 text-stone-900 shadow-[2px_2px_0px_0px_rgba(0,0,0,0.05)]' 
                    : 'bg-[#E5E5E0] border-stone-200 text-stone-800'
                  }
                `}>
                  {msg.role === 'ai' ? (
                    <CollapsibleMessage content={msg.content} />
                  ) : (
                    msg.content
                  )}
                  {msg.attachments?.length ? (
                    <ImageAttachmentStrip attachments={msg.attachments} />
                  ) : null}
                </div>
            </div>
          </div>
        ))}
        
        {/* Streaming Indicator */}
        {isStreaming && (streamingReasoning || streamingContent) && (
          <div className="flex gap-3 animate-slide-up">
             <div className="w-8 h-8 rounded-sm bg-white border border-stone-800 text-stone-900 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] flex items-center justify-center shrink-0">
                <Bot size={16} className="animate-pulse" />
             </div>
             <div className="flex flex-col max-w-[85%]">
                {streamingReasoning && (
                  <div className="mb-4 rounded-md overflow-hidden border border-stone-800 bg-[#1C1917] shadow-sm">
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#292524] border-b border-stone-800/50">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-500 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                      </span>
                      <span className="text-[10px] font-mono text-amber-500 uppercase tracking-wider font-medium">
                        System_Trace: Active
                      </span>
                    </div>
                    <div className="p-3 text-xs font-mono text-[#A8A29E] overflow-x-auto leading-relaxed max-h-48">
                      {streamingReasoning}
                      <span className="inline-block w-1.5 h-3 ml-1 bg-amber-500/50 animate-pulse align-middle"></span>
                    </div>
                  </div>
                )}
                {streamingContent && (
                  <div className="bg-white border border-stone-200 px-5 py-3.5 rounded-lg text-[15px] leading-relaxed text-stone-900 shadow-[2px_2px_0px_0px_rgba(0,0,0,0.05)] min-w-0">
                    <MarkdownRenderer content={streamingContent} />
                  </div>
                )}
             </div>
          </div>
        )}
        
        {/* Loading Indicator */}
        {isLoading && !isStreaming && (
          <div className="flex gap-3 animate-slide-up">
             <div className="w-8 h-8 rounded-sm bg-white border border-stone-800 text-stone-900 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] flex items-center justify-center shrink-0">
                <Bot size={16} className="animate-pulse" />
             </div>
             <div className="bg-white border border-stone-200 px-4 py-2 rounded text-xs font-mono text-stone-500 shadow-[2px_2px_0px_0px_rgba(0,0,0,0.05)] flex items-center gap-2">
                <span className="animate-pulse">●</span>
                ESTABLISHING_UPLINK...
             </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-stone-200 pb-safe">
        <form onSubmit={handleSubmit} className="relative space-y-2">
          {pendingImages.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {pendingImages.map((img) => (
                <div 
                  key={img.id} 
                  className="relative w-16 h-16 rounded border border-stone-200 overflow-hidden shadow-[1px_1px_0px_rgba(0,0,0,0.08)]"
                >
                  <img src={img.dataUrl} alt={img.name} className="w-full h-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removePendingImage(img.id)}
                    className="absolute -top-1 -right-1 bg-white border border-stone-200 rounded-full p-0.5 text-stone-500 hover:text-stone-800 shadow-sm"
                    title="Remove image"
                  >
                    <X size={10} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="relative flex items-center">
            <button
              type="button"
              onClick={() => imageInputRef.current?.click()}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-1.5 text-stone-500 hover:text-stone-800 hover:bg-stone-200/50 rounded transition-colors"
              title="Attach image"
            >
              <ImagePlus size={16} />
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="> Enter command or query..."
              className="w-full bg-stone-50 border border-stone-200 rounded py-3.5 pl-11 pr-14 text-[14px] font-mono outline-none focus:border-stone-400 focus:bg-white transition-all placeholder-stone-400 shadow-inner"
              onMouseDown={(e) => e.stopPropagation()}
            />
            <button 
              type="submit"
              disabled={!input.trim() || isLoading || isStreaming}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-stone-900 text-white rounded hover:bg-stone-700 disabled:opacity-50 disabled:hover:bg-stone-900 transition-colors shadow-sm touch-target h-auto w-auto"
            >
              <Send size={14} />
            </button>
            <input
              ref={imageInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => {
                handleImagesSelected(e.target.files);
                e.target.value = '';
              }}
            />
          </div>
        </form>
      </div>
    </div>
  );

  // If mobile, override floating mode to be full screen fixed
  if (mode === 'floating' && !isMobile) {
    return (
      <Rnd
        default={{
          x: window.innerWidth - 450,
          y: 80,
          width: 400,
          height: 600,
        }}
        minWidth={320}
        minHeight={400}
        bounds="window"
        className="z-50"
        dragHandleClassName="drag-handle"
        enableResizing={{
           top:false, right:false, bottom:true, left:true, 
           topRight:false, bottomRight:true, bottomLeft:true, topLeft:true 
        }}
      >
        {ChatContent}
      </Rnd>
    );
  }

  return <div className={isMobile && mode === 'floating' ? "fixed inset-0 z-[60]" : "h-full w-full"}>{ChatContent}</div>;
};
