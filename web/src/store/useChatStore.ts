import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ChatAttachment = {
  id: string;
  name: string;
  type: 'image';
  dataUrl: string;
  size: number;
  uploadedAt: number;
};

export type Message = {
  role: 'user' | 'ai';
  content: string;
  thinking?: string;
  attachments?: ChatAttachment[];
};

export type ChatConversation = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
};

type ChatState = {
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  streamingReasoning: string;
  conversations: ChatConversation[];
  currentConversationId: string | null;

  setLoading: (v: boolean) => void;
  setStreaming: (v: boolean) => void;
  appendContent: (chunk: string) => void;
  appendReasoning: (chunk: string) => void;
  addUserMessage: (content: string, attachments?: ChatAttachment[]) => void;
  addAiMessage: (content: string, thinking?: string) => void;
  finalizeStream: () => void;
  reset: () => void;
  startNewChat: () => void;
  loadConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, title: string) => void;
  buildImageContext: (pending?: ChatAttachment[]) => string;
};

const greeting: Message = { role: 'ai', content: "Hello! I'm your research mentor. How can I help you refine your hypothesis today?" };

const generatePlaceholderTitle = () => {
  const now = new Date();
  const hh = now.getHours().toString().padStart(2, '0');
  const mm = now.getMinutes().toString().padStart(2, '0');
  return `New chat ${hh}:${mm}`;
};

const upsertConversation = (convos: ChatConversation[], convo: ChatConversation) => {
  const idx = convos.findIndex(c => c.id === convo.id);
  if (idx === -1) return [...convos, convo];
  const copy = [...convos];
  copy[idx] = convo;
  return copy;
};

export const useChatStore = create<ChatState>()(persist((set, get) => ({
  messages: [greeting],
  isLoading: false,
  isStreaming: false,
  streamingContent: "",
  streamingReasoning: "",
  conversations: [],
  currentConversationId: null,

  setLoading: (v) => set({ isLoading: v }),
  setStreaming: (v) => set({ 
    isStreaming: v, 
    streamingContent: v ? "" : get().streamingContent,
    streamingReasoning: v ? "" : get().streamingReasoning,
  }),
  appendContent: (chunk) => set((state) => ({ streamingContent: state.streamingContent + chunk })),
  appendReasoning: (chunk) => set((state) => ({ streamingReasoning: state.streamingReasoning + chunk })),

  addUserMessage: (content, attachments = []) => {
    const state = get();
    const hasConversation = Boolean(state.currentConversationId);
    const convoId = hasConversation ? state.currentConversationId! : `chat-${Date.now()}`;
    const isFirstUser = state.messages.filter(m => m.role === 'user').length === 0;
    const title = isFirstUser
      ? generatePlaceholderTitle()
      : (state.conversations.find(c => c.id === convoId)?.title || 'Untitled chat');
    
    const updatedMessages = [...state.messages, { 
      role: 'user', 
      content, 
      ...(attachments.length ? { attachments } : {}), 
    }];
    const convo: ChatConversation = {
      id: convoId,
      title,
      messages: updatedMessages,
      createdAt: hasConversation 
        ? (state.conversations.find(c => c.id === convoId)?.createdAt || Date.now())
        : Date.now(),
      updatedAt: Date.now(),
    };

    set({
      messages: updatedMessages,
      currentConversationId: convoId,
      conversations: upsertConversation(state.conversations, convo),
    });
  },

  addAiMessage: (content, thinking) => {
    const state = get();
    const convoId = state.currentConversationId ?? `chat-${Date.now()}`;
    const updatedMessages = [...state.messages, { role: 'ai', content, thinking }];
    const existing = state.conversations.find(c => c.id === convoId);
    const convo: ChatConversation = {
      id: convoId,
      title: existing?.title || 'Untitled chat',
      messages: updatedMessages,
      createdAt: existing?.createdAt || Date.now(),
      updatedAt: Date.now(),
    };
    set({
      messages: updatedMessages,
      currentConversationId: convoId,
      conversations: upsertConversation(state.conversations, convo),
    });
  },

  finalizeStream: () => {
    const state = get();
    if (state.streamingContent.trim() || state.streamingReasoning.trim()) {
      let finalContent = state.streamingContent.trim();
      let finalReasoning = state.streamingReasoning.trim();
      
      // Fallback: Parse <thinking> tags from content if no reasoning was streamed
      if (!finalReasoning && finalContent) {
        const thinkMatch = finalContent.match(/<thinking>([\s\S]*?)<\/thinking>/i);
        if (thinkMatch) {
          finalReasoning = thinkMatch[1].trim();
          finalContent = finalContent.replace(/<thinking>[\s\S]*?<\/thinking>/gi, '').trim();
        }
      }
      
      const updatedMessages = [...state.messages, {
        role: 'ai',
        content: finalContent || "(No content)",
        thinking: finalReasoning || undefined,
      }];

      const convoId = state.currentConversationId ?? `chat-${Date.now()}`;
      const existing = state.conversations.find(c => c.id === convoId);
      const convo: ChatConversation = {
        id: convoId,
        title: existing?.title || 'Untitled chat',
        messages: updatedMessages,
        createdAt: existing?.createdAt || Date.now(),
        updatedAt: Date.now(),
      };

      set({
        messages: updatedMessages,
        streamingContent: "",
        streamingReasoning: "",
        isStreaming: false,
        currentConversationId: convoId,
        conversations: upsertConversation(state.conversations, convo),
      });
    }
  },

  reset: () => {
    set({
      messages: [greeting],
      isLoading: false,
      isStreaming: false,
      streamingContent: "",
      streamingReasoning: "",
      currentConversationId: null,
    });
  },

  startNewChat: () => set({
    messages: [greeting],
    isLoading: false,
    isStreaming: false,
    streamingContent: "",
    streamingReasoning: "",
    currentConversationId: null,
  }),

  loadConversation: (id) => {
    const convo = get().conversations.find(c => c.id === id);
    if (!convo) return;
    set({
      messages: convo.messages.length ? convo.messages : [greeting],
      currentConversationId: convo.id,
      isLoading: false,
      isStreaming: false,
      streamingContent: "",
      streamingReasoning: "",
    });
  },

  deleteConversation: (id) => {
    set((state) => {
      const remaining = state.conversations.filter(c => c.id !== id);
      const resetToGreeting = state.currentConversationId === id;
      return {
        conversations: remaining,
        ...(resetToGreeting ? {
          currentConversationId: null,
          messages: [greeting],
          isLoading: false,
          isStreaming: false,
          streamingContent: "",
          streamingReasoning: "",
        } : {}),
      };
    });
  },

  renameConversation: (id, title) => {
    set((state) => ({
      conversations: state.conversations.map(c => c.id === id ? { ...c, title, updatedAt: Date.now() } : c),
      ...(state.currentConversationId === id ? { currentConversationId: id } : {}),
      ...(state.currentConversationId === id ? { messages: state.messages } : {}),
    }));
  },

  buildImageContext: (pending = []) => {
    const state = get();
    const existing = state.messages.flatMap((msg) => msg.attachments || []).filter((att) => att.type === 'image');
    const combined = [...existing, ...pending];
    const seen = new Set<string>();
    const unique = combined.filter((att) => {
      if (seen.has(att.id)) return false;
      seen.add(att.id);
      return true;
    });

    if (unique.length === 0) return "";

    const safeAttachments = unique.slice(-6); // keep the most recent few to avoid bloating prompts
    return safeAttachments
      .map((att) => {
        const snippet = att.dataUrl.length > 200 ? `${att.dataUrl.slice(0, 200)}...` : att.dataUrl;
        const kbSize = (att.size / 1024).toFixed(1);
        return [
          `Image: ${att.name}`,
          `Uploaded: ${new Date(att.uploadedAt).toISOString()}`,
          `Size: ${kbSize} KB`,
          `DataURL (truncated): ${snippet}`,
        ].join("\n");
      })
      .join("\n\n");
  }
}), { name: 'mentor-chat-history' }));
