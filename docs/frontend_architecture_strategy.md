# Frontend Architecture & Design Strategy: Research Canvas

## 1. Executive Summary
**Goal**: Create an intuitive, infinite-canvas research interface for undergraduates and beginners.
**Core Metaphor**: "Spatial Research" — moving away from linear chat logs to a map of thoughts, conversations, and resources.
**Key Interactions**: Branching conversations, visual clustering of related papers, and drag-and-drop organization.

## 2. Technology Stack

### Core Framework
*   **Framework**: **Next.js 15 (App Router)**
    *   *Why*: Industry standard, built-in routing, server-side rendering (useful for initial load performance), and easy deployment.
*   **Language**: **TypeScript**
    *   *Why*: Essential for maintainable architecture, especially with complex state objects like graphs and nodes.

### Canvas Engine
*   **Library**: **React Flow (now XYFlow)**
    *   *Decision*: **React Flow** over Tldraw.
    *   *Reasoning*:
        *   **React Flow** is optimized for *node-based* graphs with complex interactive content inside nodes (forms, chat lists, buttons).
        *   **Tldraw** is superior for freehand drawing, but harder to instrument with complex DOM elements like a scrolling chat window within a shape.
        *   React Flow handles the "Branching" logic (edges, handles) natively, which is core to the "Branching conversations" requirement.

### State Management
*   **Global State**: **Zustand**
    *   *Why*: Lightweight, hooks-based, and has a first-party integration with React Flow (`useStore`). It avoids the boilerplate of Redux and the complexity of Context for high-frequency canvas updates.
*   **Local Persistence**: **idb-keyval** (IndexedDB wrapper)
    *   *Why*: To auto-save the canvas state locally so users don't lose work on refresh.

### Styling & UI Components
*   **Styling System**: **Tailwind CSS**
    *   *Why*: Rapid development, scoped styles via utility classes.
*   **Component Library**: **shadcn/ui** (built on Radix UI)
    *   *Why*: Accessible, headless (customizable), and copy-pasteable. Provides high-quality accessible primitives (Dropdowns, Dialogs, Tooltips) needed for node actions.
*   **Icons**: **Lucide React**
    *   *Why*: Clean, consistent stroke-width icons that match the "Modern/Academic" aesthetic.

## 3. UI/UX Strategy

### Visual Aesthetic
*   **Theme**: **"Deep Focus" Dark Mode**.
    *   Background: Dark Slate/Charcoal (`#0f172a` or similar).
    *   Nodes: Slightly lighter cards with subtle borders (`border-slate-700`).
    *   Accents: Muted Indigo/Violet for active states (scholarly but modern).
*   **Typography**: Sans-serif (Inter or Geist Sans) for readability. Monospace for code snippets within chats.

### Interaction Model
1.  **The "Seed"**: The canvas starts with a single central node (e.g., "Research Topic?").
2.  **Branching**:
    *   User types in a Chat Node.
    *   AI replies.
    *   User can click a specific message and drag out a handle to "Branch" the conversation into a new direction.
    *   *Visual*: A Bezier curve connects the original message to the new Chat Node.
3.  **Research Cycles**:
    *   Group related nodes (Chat + 3 Papers) using **Group Nodes** (a React Flow feature).
    *   Visual cues: Dotted bounding boxes around clusters representing a "Line of Inquiry".

### Accessibility (A11y)
*   **Keyboard Navigation**: Ensure nodes can be tabbed through.
*   **Screen Readers**: Use `aria-label` on handles and nodes. React Flow has basic a11y, but custom nodes need care.
*   **Contrast**: Ensure text-on-card contrast meets WCAG AA.

## 4. Key Components Architecture

### A. The Canvas Wrapper (`ResearchCanvas.tsx`)
*   Initializes the React Flow instance.
*   Handles global events (drag over, drop).
*   Renders the `Background` (dots/grid) and `Controls` (zoom/fit).

### B. Custom Node Types
1.  **`ChatNode`**:
    *   **Header**: Title (auto-generated or editable), Close button, "Branch" button.
    *   **Body**: Scrollable list of `Message` components (User/AI).
    *   **Input**: Text area at bottom.
    *   **Handles**: Source handle (right) for branching, Target handle (left) for incoming connection.
2.  **`PaperNode`**:
    *   **Visual**: Card looking like a citation.
    *   **Content**: Title, Authors, Year, Abstract (collapsible).
    *   **Action**: "Read" (opens modal), "Cite".
3.  **`NoteNode`**:
    *   Simple Markdown editor for sticky notes.

### C. The Toolbar (`CanvasToolbar.tsx`)
*   Floating palette (bottom-center or left-vertical).
*   Tools: Select (cursor), Hand (pan), Add Note, Add Chat, Magic Search (AI trigger).

### D. The Minimap (`NavigationMap.tsx`)
*   Bottom-right corner.
*   Shows high-level cluster structure.

## 5. Proposed File Structure

```text
web/
├── public/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Root layout (providers)
│   │   └── page.tsx         # Main Canvas Page
│   ├── components/
│   │   ├── canvas/
│   │   │   ├── nodes/
│   │   │   │   ├── ChatNode.tsx
│   │   │   │   ├── PaperNode.tsx
│   │   │   │   └── NoteNode.tsx
│   │   │   ├── edges/
│   │   │   │   └── BranchEdge.tsx
│   │   │   ├── ResearchCanvas.tsx
│   │   │   └── Toolbar.tsx
│   │   ├── ui/              # shadcn components (Button, Card, etc.)
│   │   └── providers/
│   │       └── ReactFlowProvider.tsx
│   ├── lib/
│   │   ├── store.ts         # Zustand store (nodes, edges, user state)
│   │   ├── types.ts         # Node/Edge type definitions
│   │   └── utils.ts
│   └── styles/
│       └── globals.css      # Tailwind directives
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## 6. Implementation Phase 1 Checklist
1.  [ ] Initialize Next.js project in `web/`.
2.  [ ] Install `reactflow` (or `@xyflow/react`), `zustand`, `lucide-react`.
3.  [ ] Set up `ResearchCanvas` with empty state.
4.  [ ] Create the basic `ChatNode` visual component.
5.  [ ] Implement "Add Node" functionality via Zustand.
