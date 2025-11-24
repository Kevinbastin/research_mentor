import { create } from 'zustand';
import {
  Connection,
  Edge,
  EdgeChange,
  Node,
  NodeChange,
  addEdge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
} from '@xyflow/react';

type RFState = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  addNode: (node: Node) => void;
};

// Initial Mock Data
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'chat',
    position: { x: 0, y: 0 },
    data: { 
      prompt: "What is the state of the art in LLM alignment?",
      response: "Current SOTA involves RLHF, DPO, and Constitutional AI approaches. Key papers include InstructGPT and LLaMA 2." 
    },
  },
  {
    id: '2',
    type: 'paper',
    position: { x: 400, y: -100 },
    data: { 
      title: "Training language models to follow instructions with human feedback",
      authors: "Ouyang et al.",
      year: "2022",
      citations: 4500,
      abstract: "We show that fine-tuning with human feedback helps align language models with user intent..."
    },
  },
  {
    id: '3',
    type: 'paper',
    position: { x: 400, y: 150 },
    data: { 
      title: "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
      authors: "Rafailov et al.",
      year: "2023",
      citations: 890,
      abstract: "DPO optimizes the policy directly to satisfy human preferences without explicit reward modeling..."
    },
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e1-3', source: '1', target: '3', animated: true },
];

export const useResearchStore = create<RFState>((set, get) => ({
  nodes: initialNodes,
  edges: initialEdges,
  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },
  onConnect: (connection: Connection) => {
    set({
      edges: addEdge(connection, get().edges),
    });
  },
  addNode: (node: Node) => {
    set({
      nodes: [...get().nodes, node],
    });
  },
}));
