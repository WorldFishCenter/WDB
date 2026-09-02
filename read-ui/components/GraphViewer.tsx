"use client";

import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import type { Association, Mode, Confidence } from "@/lib/contract";
import styles from "./graph.module.scss";

// Premium community colors aligned with WorldFish design tokens
export const COMMUNITY_COLORS = [
  "#508fda", // 0: Peskas Platform & Scaling (Primary Blue)
  "#f28e2b", // 1: Digital Transformation Accelerator (Orange)
  "#e15759", // 2: SSF Data Harmonization Framework (Red)
  "#76b7b2", // 3: WIO Harmonized Catch/Effort Data (Teal)
  "#edc948", // 4: FASA Global Scaling
  "#edc948", // 5: FASA Feed Formulation (Yellow)
  "#b07aa1", // 6: Timor-Leste Nutrition RCT (Purple)
  "#ff9da7", // 7: PondCube Water-Quality Data (Pink)
  "#9c755f", // 8: CGIAR Data Ecosystem & FAIR (Brown)
  "#8d99ae", // 9: Fallback (Slate)
];

export interface Node {
  id: string;
  label: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  fx?: number;
  fy?: number;
  community: number;
  file_type?: string;
  degree: number;
}

export interface Link {
  source: string;
  target: string;
  relation: string;
  confidence: Confidence;
}

interface GraphViewerProps {
  associations: Association[];
  globalNodeMap?: Map<string, { label: string; community: number; file_type?: string; source_file?: string }>;
  onSelectNode: (nodeId: string | null) => void;
  selectedNodeId: string | null;
  onViewSource?: (path: string) => void;
}


export function GraphViewer({
  associations,
  globalNodeMap,
  onSelectNode,
  selectedNodeId,
  onViewSource,
}: GraphViewerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Dynamic container dimensions via ResizeObserver
  const [containerSize, setContainerSize] = useState({ width: 800, height: 500 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setContainerSize({ width, height });
        }
      }
    });
    ro.observe(el);

    // Initial measurement
    const rect = el.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      setContainerSize({ width: rect.width, height: rect.height });
    }

    return () => ro.disconnect();
  }, []);
  
  // Transform state for pan & zoom
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const dragTranslateStart = useRef({ x: 0, y: 0 });

  // Hover states
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [hoveredLinkId, setHoveredLinkId] = useState<string | null>(null);

  // Active drag state for nodes
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);

  // Parse nodes and links from associations, using dynamic container size
  const { initialNodes, links } = useMemo(() => {
    const nodeIds = new Set<string>();
    const parsedLinks: Link[] = [];

    associations.forEach((assoc) => {
      const src = assoc.source;
      const tgt = assoc.target;
      if (src && tgt) {
        nodeIds.add(src);
        nodeIds.add(tgt);
        parsedLinks.push({
          source: src,
          target: tgt,
          relation: assoc.relation || "related",
          confidence: assoc.confidence || "EXTRACTED",
        });
      }
    });

    // Compute degrees
    const degrees: Record<string, number> = {};
    nodeIds.forEach((id) => {
      degrees[id] = 0;
    });
    parsedLinks.forEach((link) => {
      if (degrees[link.source] !== undefined) degrees[link.source]++;
      if (degrees[link.target] !== undefined) degrees[link.target]++;
    });

    const width = containerSize.width;
    const height = containerSize.height;

    const parsedNodes: Node[] = Array.from(nodeIds).map((id, index) => {
      const globalMeta = globalNodeMap?.get(id);
      
      // Heuristics for node label if metadata not loaded
      let label = id;
      if (globalMeta?.label) {
        label = globalMeta.label;
      } else {
        // Clean label
        label = id
          .replace(/^(shared_|ssf_research_|peskas_|data_harmonization_|dta_)/, "")
          .replace(/_/g, " ");
        // Title case
        label = label.charAt(0).toUpperCase() + label.slice(1);
      }

      // Arrange nodes in a circle initially to prevent stacking
      const angle = (index / nodeIds.size) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.35;
      
      return {
        id,
        label,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        community: globalMeta?.community ?? (id.includes("peskas") ? 0 : id.includes("harmonization") ? 2 : id.includes("dta") ? 1 : 9),
        file_type: globalMeta?.file_type,
        degree: degrees[id] || 1,
      };
    });

    return { initialNodes: parsedNodes, links: parsedLinks };
  }, [associations, globalNodeMap, containerSize]);

  const [nodes, setNodes] = useState<Node[]>([]);
  const nodesRef = useRef<Node[]>([]);

  // Synchronize internal nodes when associations change
  useEffect(() => {
    setNodes(initialNodes);
    nodesRef.current = initialNodes;
    
    // Reset transform to center
    setTransform({ x: 0, y: 0, k: 1 });
  }, [initialNodes]);

  // Verlet integration physics engine
  useEffect(() => {
    if (nodesRef.current.length === 0) return;


    let animFrameId: number;
    
    const kRepulsion = 2500;
    const kAttraction = 0.05;
    const restLength = 100;
    const kGravity = 0.02;
    const damping = 0.82;
    const width = containerSize.width;
    const height = containerSize.height;

    const tick = () => {
      const currentNodes = [...nodesRef.current];
      if (currentNodes.length === 0) return;

      const nodeMap = new Map<string, Node>();
      currentNodes.forEach((n) => nodeMap.set(n.id, n));

      // 1. Repulsion between all nodes
      for (let i = 0; i < currentNodes.length; i++) {
        const n1 = currentNodes[i];
        for (let j = i + 1; j < currentNodes.length; j++) {
          const n2 = currentNodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy + 1; // avoid division by zero
          const dist = Math.sqrt(distSq);

          if (dist < 250) {
            // Stronger repulsion if nodes are very close
            const force = (kRepulsion / distSq) * (dist < 40 ? 3 : 1);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }
        }
      }

      // 2. Attraction along links
      links.forEach((link) => {
        const sNode = nodeMap.get(link.source);
        const tNode = nodeMap.get(link.target);
        if (sNode && tNode) {
          const dx = tNode.x - sNode.x;
          const dy = tNode.y - sNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = kAttraction * (dist - restLength);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          sNode.vx += fx;
          sNode.vy += fy;
          tNode.vx -= fx;
          tNode.vy -= fy;
        }
      });

      // 3. Gravity pulling nodes towards center
      const cx = width / 2;
      const cy = height / 2;
      currentNodes.forEach((node) => {
        const dx = cx - node.x;
        const dy = cy - node.y;
        node.vx += dx * kGravity;
        node.vy += dy * kGravity;
      });

      // 4. Update coordinates with friction/damping
      const updatedNodes = currentNodes.map((node) => {
        if (node.fx !== undefined && node.fy !== undefined) {
          return {
            ...node,
            x: node.fx,
            y: node.fy,
            vx: 0,
            vy: 0,
          };
        } else {
          let vx = node.vx * damping;
          let vy = node.vy * damping;
          
          // Speed cap to prevent explosion
          const speed = Math.sqrt(vx * vx + vy * vy);
          if (speed > 15) {
            vx = (vx / speed) * 15;
            vy = (vy / speed) * 15;
          }

          return {
            ...node,
            x: node.x + vx,
            y: node.y + vy,
            vx,
            vy,
          };
        }
      });

      nodesRef.current = updatedNodes;
      setNodes(updatedNodes);

      animFrameId = requestAnimationFrame(tick);
    };

    animFrameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameId);
  }, [links, initialNodes, containerSize]);

  // Handle canvas drag (pan)
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    // If clicking a node, don't drag the canvas
    if ((e.target as SVGElement).closest(".node-group")) return;

    setIsDraggingCanvas(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    dragTranslateStart.current = { x: transform.x, y: transform.y };
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (isDraggingCanvas) {
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      setTransform((prev) => ({
        ...prev,
        x: dragTranslateStart.current.x + dx,
        y: dragTranslateStart.current.y + dy,
      }));
    } else if (draggedNodeId) {
      // Node drag handling
      const svg = svgRef.current;
      if (!svg) return;

      const rect = svg.getBoundingClientRect();
      // Mouse coordinates relative to SVG container
      const mX = e.clientX - rect.left;
      const mY = e.clientY - rect.top;

      // Convert mouse coordinates back through the SVG transform to graph coordinates
      const graphX = (mX - transform.x) / transform.k;
      const graphY = (mY - transform.y) / transform.k;

      // Update fx/fy in ref
      nodesRef.current = nodesRef.current.map((n) => {
        if (n.id === draggedNodeId) {
          return { ...n, fx: graphX, fy: graphY, x: graphX, y: graphY };
        }
        return n;
      });
    }
  };

  const handleMouseUp = () => {
    setIsDraggingCanvas(false);
    if (draggedNodeId) {
      // Release node from force pinning
      nodesRef.current = nodesRef.current.map((n) => {
        if (n.id === draggedNodeId) {
          const { fx, fy, ...rest } = n;
          return rest as Node;
        }
        return n;
      });
      setDraggedNodeId(null);
    }
  };

  // Zoom handling
  const handleWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const svg = svgRef.current;
    if (!svg) return;

    const rect = svg.getBoundingClientRect();
    const mX = e.clientX - rect.left;
    const mY = e.clientY - rect.top;

    const zoomFactor = 1.05;
    const nextK = e.deltaY < 0 ? transform.k * zoomFactor : transform.k / zoomFactor;
    
    // Constraint zoom level
    const k = Math.max(0.3, Math.min(3, nextK));

    // Zoom into mouse pointer coordinate
    const dx = mX - transform.x;
    const dy = mY - transform.y;
    const x = mX - dx * (k / transform.k);
    const y = mY - dy * (k / transform.k);

    setTransform({ x, y, k });
  };

  // Node Drag Start
  const handleNodeDragStart = (nodeId: string) => {
    setDraggedNodeId(nodeId);
    onSelectNode(nodeId);
  };

  // Helpers to highlight connected elements
  const connectedNodeIds = useMemo(() => {
    if (!hoveredNodeId && !selectedNodeId) return null;
    const activeId = hoveredNodeId || selectedNodeId;
    const ids = new Set<string>([activeId!]);
    links.forEach((l) => {
      if (l.source === activeId) ids.add(l.target);
      if (l.target === activeId) ids.add(l.source);
    });
    return ids;
  }, [hoveredNodeId, selectedNodeId, links]);

  // Selected node metadata
  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  const selectedNodeMetadata = useMemo(() => {
    if (!selectedNodeId) return null;
    return globalNodeMap?.get(selectedNodeId) || null;
  }, [selectedNodeId, globalNodeMap]);

  return (
    <div className={styles.container}>
      <div className={styles.canvasWrap} ref={containerRef}>
        <svg
          ref={svgRef}
          className={styles.svg}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          {/* Arrow markers for directed edges */}
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M0,0 L10,5 L0,10 z" fill="var(--wf-color-gray-400)" />
            </marker>
            <marker
              id="arrow-active"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M0,0 L10,5 L0,10 z" fill="var(--wf-accent)" />
            </marker>
          </defs>

          {/* Background grid */}
          <rect width="100%" height="100%" fill="none" pointerEvents="all" />

          <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
            {/* Draw Links */}
            {links.map((link, i) => {
              const sourceNode = nodes.find((n) => n.id === link.source);
              const targetNode = nodes.find((n) => n.id === link.target);

              if (!sourceNode || !targetNode) return null;

              const isHovered =
                hoveredLinkId === `${link.source}-${link.target}-${i}` ||
                (hoveredNodeId && (link.source === hoveredNodeId || link.target === hoveredNodeId));

              const isDimmed =
                connectedNodeIds &&
                (!connectedNodeIds.has(link.source) || !connectedNodeIds.has(link.target));

              return (
                <g
                  key={`${link.source}-${link.target}-${i}`}
                  className={`${styles.linkGroup} ${isHovered ? styles.linkActive : ""} ${
                    isDimmed ? styles.linkDimmed : ""
                  }`}
                  onMouseEnter={() => setHoveredLinkId(`${link.source}-${link.target}-${i}`)}
                  onMouseLeave={() => setHoveredLinkId(null)}
                >
                  <line
                    x1={sourceNode.x}
                    y1={sourceNode.y}
                    x2={targetNode.x}
                    y2={targetNode.y}
                    stroke={isHovered ? "var(--wf-accent)" : "var(--wf-border)"}
                    strokeWidth={isHovered ? 2.5 : 1.5}
                    strokeDasharray={link.confidence === "INFERRED" ? "4,4" : undefined}
                    markerEnd={isHovered ? "url(#arrow-active)" : "url(#arrow)"}
                  />
                  {/* Invisible thick line for easier hover interactions */}
                  <line
                    x1={sourceNode.x}
                    y1={sourceNode.y}
                    x2={targetNode.x}
                    y2={targetNode.y}
                    stroke="transparent"
                    strokeWidth={10}
                    className={styles.hitArea}
                  />
                  {/* Relation name on link hover */}
                  {isHovered && (
                    <text
                      x={(sourceNode.x + targetNode.x) / 2}
                      y={(sourceNode.y + targetNode.y) / 2 - 6}
                      className={styles.linkLabel}
                      textAnchor="middle"
                    >
                      {link.relation}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Draw Nodes */}
            {nodes.map((node) => {
              const isSelected = selectedNodeId === node.id;
              const isHovered = hoveredNodeId === node.id;
              const isDimmed = connectedNodeIds && !connectedNodeIds.has(node.id);
              
              // Base radius starts at 10 and scales with node connection degree
              const r = 8 + Math.min(node.degree * 2, 10);
              const color = COMMUNITY_COLORS[node.community % COMMUNITY_COLORS.length];

              return (
                <g
                  key={node.id}
                  className={`${styles.nodeGroup} ${isSelected ? styles.nodeSelected : ""} ${
                    isHovered ? styles.nodeHover : ""
                  } ${isDimmed ? styles.nodeDimmed : ""}`}
                  transform={`translate(${node.x}, ${node.y})`}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  onMouseDown={(e) => {
                    e.stopPropagation();
                    handleNodeDragStart(node.id);
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectNode(node.id);
                  }}
                >
                  {/* Pulsing halo around selected node */}
                  {isSelected && (
                    <circle r={r + 6} fill="none" stroke="var(--wf-accent)" strokeWidth={2} className={styles.pulse} />
                  )}
                  
                  {/* Base node circle */}
                  <circle
                    r={r}
                    fill={color}
                    stroke={isSelected || isHovered ? "var(--wf-color-white)" : "var(--wf-bg)"}
                    strokeWidth={isSelected || isHovered ? 2.5 : 1.5}
                    className={styles.nodeCircle}
                  />
                  
                  {/* Entity icon inside node if zoom level allows */}
                  {node.file_type === "document" && <text y={3} textAnchor="middle" fill="#fff" fontSize="8" pointerEvents="none">📄</text>}
                  {node.file_type === "code" && <text y={3} textAnchor="middle" fill="#fff" fontSize="8" pointerEvents="none">💻</text>}

                  {/* Node label */}
                  <text
                    y={r + 14}
                    textAnchor="middle"
                    className={styles.nodeLabel}
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>

        {/* Canvas overlays for zoom controls */}
        <div className={styles.controls}>
          <button onClick={() => setTransform((prev) => ({ ...prev, k: Math.min(3, prev.k * 1.2) }))} title="Zoom In">+</button>
          <button onClick={() => setTransform((prev) => ({ ...prev, k: Math.max(0.3, prev.k / 1.2) }))} title="Zoom Out">-</button>
          <button onClick={() => setTransform({ x: 0, y: 0, k: 1 })} title="Reset View">⟲</button>
        </div>
      </div>

      {/* Selected Node Inspector Card */}
      {selectedNode && (
        <div className={styles.inspector}>
          <div className={styles.inspectorHead}>
            <span className={styles.inspectorTitle}>{selectedNode.label}</span>
            <button className={styles.closeBtn} onClick={() => onSelectNode(null)}>✕</button>
          </div>
          <div className={styles.inspectorBody}>
            <div className={styles.metaRow}>
              <span className={styles.metaBadge} style={{ backgroundColor: `${COMMUNITY_COLORS[selectedNode.community % COMMUNITY_COLORS.length]}22`, color: COMMUNITY_COLORS[selectedNode.community % COMMUNITY_COLORS.length] }}>
                {selectedNodeMetadata?.file_type || "concept"}
              </span>
              <span className={styles.metaText}>
                Degree: {selectedNode.degree} connections
              </span>
            </div>
            {selectedNodeMetadata?.source_file && (
              <div className={styles.sourceRow}>
                <span className={styles.sourceLabel}>Source File:</span>
                <span className={styles.sourcePath}>{selectedNodeMetadata.source_file}</span>
                {onViewSource && (
                  <button 
                    className={styles.viewSourceBtn}
                    onClick={() => onViewSource(selectedNodeMetadata.source_file!)}
                  >
                    View Source Note
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
