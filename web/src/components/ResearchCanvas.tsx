"use client";

import { useCallback, useMemo, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  NodeTypes,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useResearchStore } from '@/store/useResearchStore';
import ChatNode from './ChatNode';
import PaperNode from './PaperNode';
import { TheDock } from './TheDock';

const CanvasContent = () => {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode
  } = useResearchStore();

  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();

  const nodeTypes = useMemo<NodeTypes>(() => ({
    chat: ChatNode,
    paper: PaperNode,
  }), []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const dataString = event.dataTransfer.getData('application/json');

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const data = JSON.parse(dataString);
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: Math.random().toString(36).substring(7),
        type,
        position,
        data: type === 'paper' ? data : { ...data, prompt: data.prompt, response: data.response },
      };

      addNode(newNode);
    },
    [screenToFlowPosition, addNode],
  );

  return (
    <div className="h-full w-full bg-slate-950 text-white" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        onDragOver={onDragOver}
        onDrop={onDrop}
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

const ResearchCanvas = () => {
    return (
        <ReactFlowProvider>
            <CanvasContent />
        </ReactFlowProvider>
    );
}

export default ResearchCanvas;
