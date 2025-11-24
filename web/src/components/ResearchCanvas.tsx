"use client";

import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useResearchStore } from '@/store/useResearchStore';
import ChatNode from './ChatNode';
import PaperNode from './PaperNode';
import { TheDock } from './TheDock';

const ResearchCanvas = () => {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
  } = useResearchStore();

  const nodeTypes = useMemo<NodeTypes>(() => ({
    chat: ChatNode,
    paper: PaperNode,
  }), []);

  return (
    <div className="h-screen w-screen bg-slate-950 text-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-slate-950"
        minZoom={0.1}
        maxZoom={1.5}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
      >
        <Background 
            variant={BackgroundVariant.Dots} 
            gap={24} 
            size={1.5} 
            color="#334155" 
        />
        <Controls className="!bg-slate-900 !border-slate-800 [&>button]:!border-slate-800 [&>button]:!text-slate-400 [&>button:hover]:!bg-slate-800" />
        <TheDock />
      </ReactFlow>
    </div>
  );
};

export default ResearchCanvas;
