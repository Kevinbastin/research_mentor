import { create } from 'zustand';

export type PaperItem = {
  id: string;
  title: string;
  authors: string;
  year: string;
  abstract: string;
  citations: number;
  tags: string[];
};

export type ThreadItem = {
  id: string;
  title: string;
  lastActive: string;
  preview: string;
};

type LibraryState = {
  papers: PaperItem[];
  threads: ThreadItem[];
  addPaper: (paper: PaperItem) => void;
  addThread: (thread: ThreadItem) => void;
};

// Mock Initial Data
const initialPapers: PaperItem[] = [
    {
        id: 'p1',
        title: "Attention Is All You Need",
        authors: "Vaswani et al.",
        year: "2017",
        citations: 80000,
        abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        tags: ["Transformer", "NLP"]
    },
    {
        id: 'p2',
        title: "Deep Residual Learning for Image Recognition",
        authors: "He et al.",
        year: "2016",
        citations: 150000,
        abstract: "We present a residual learning framework to ease the training of networks that are substantially deeper...",
        tags: ["CV", "ResNet"]
    }
];

const initialThreads: ThreadItem[] = [
    { id: 't1', title: "Research Methods Help", lastActive: "2 mins ago", preview: "How do I structure a..." },
    { id: 't2', title: "Transformer Arch", lastActive: "1 day ago", preview: "Explaining QKV..." }
];

export const useLibraryStore = create<LibraryState>((set) => ({
  papers: initialPapers,
  threads: initialThreads,
  addPaper: (paper) => set((state) => ({ papers: [...state.papers, paper] })),
  addThread: (thread) => set((state) => ({ threads: [...state.threads, thread] })),
}));
