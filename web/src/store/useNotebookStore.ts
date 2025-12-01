import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type NotebookNote = {
  id: string;
  title: string;
  content: any; // Tiptap JSON
  createdAt: string; // ISO string
  updatedAt: string; // ISO string
};

type NotebookState = {
  content: any | null;
  lastUpdatedAt: string | null;
  notes: NotebookNote[];
  setContent: (content: any) => void;
  saveNote: (title?: string) => NotebookNote;
  loadNote: (id: string) => NotebookNote | undefined;
  deleteNote: (id: string) => void;
};

export const useNotebookStore = create<NotebookState>()(
  persist(
    (set, get) => ({
      content: null,
      lastUpdatedAt: null,
      notes: [],

      setContent: (content) =>
        set(() => ({
          content,
          lastUpdatedAt: new Date().toISOString(),
        })),

      saveNote: (title) => {
        const state = get();
        const id = `note-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
        const noteTitle =
          title ||
          (state.content?.content?.find?.((node: any) => node.type === 'heading')?.content?.[0]?.text as
            | string
            | undefined) ||
          'Untitled note';
        const newNote: NotebookNote = {
          id,
          title: noteTitle,
          content: state.content,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        set({
          notes: [newNote, ...state.notes].slice(0, 100), // keep reasonable cap
        });
        return newNote;
      },

      loadNote: (id) => {
        const note = get().notes.find((n) => n.id === id);
        if (note) {
          set({
            content: note.content,
            lastUpdatedAt: new Date().toISOString(),
          });
        }
        return note;
      },

      deleteNote: (id) => {
        set((state) => ({
          notes: state.notes.filter((n) => n.id !== id),
        }));
      },
    }),
    {
      name: 'notebook-store',
      partialize: (state) => ({
        content: state.content,
        lastUpdatedAt: state.lastUpdatedAt,
        notes: state.notes,
      }),
    }
  )
);
