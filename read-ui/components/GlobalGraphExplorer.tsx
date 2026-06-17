"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import type { Confidence } from "@/lib/contract";
import { COMMUNITY_COLORS, type Node, type Link } from "./GraphViewer";
import { useSourceViewer } from "./source/SourceViewerProvider";
import styles from "./graph.module.scss";

interface GlobalGraphExplorerProps {
  onClose: () => void;
  graphData: {
    nodes: any[];
    links: any[];
    graph?: { hyperedges?: any[] };
  } | null;
}

export const COMMUNITY_NAMES: Record<number, string> = {
  0: "Peskas Platform & Scaling",
  1: "Digital Transformation Accelerator",
  2: "SSF Data Harmonization Framework",
  3: "WIO Harmonized Catch/Effort Data",
  4: "FASA Global Scaling",
  5: "FASA Feed Formulation",
  6: "Timor-Leste Nutrition RCT",
  7: "PondCube Water-Quality Data",
  8: "CGIAR Data Ecosystem & FAIR",
  9: "General Knowledge",
};

export function GlobalGraphExplorer({ onClose, graphData }: GlobalGraphExplorerProps) {
  const { openSource } = useSourceViewer();
  const svgRef = useRef<SVGSVGElement>(null);

  // States
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 0.6 });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Community visibility states
  const [hiddenCommunities, setHiddenCommunities] = useState<Set<number>>(new Set());

  // Refs for dragging
  const dragStart = useRef({ x: 0, y: 0 });
  const dragTranslateStart = useRef({ x: 0, y: 0 });

  // 1. Process Raw Data from graph.json
  const { initialNodes, initialLinks, hyperedges } = useMemo(() => {
    if (!graphData) return { initialNodes: [], initialLinks: [], hyperedges: [] };

    // Compute degrees
    const degrees: Record<string, number> = {};
    graphData.nodes.forEach((n) => {
      degrees[n.id] = 0;
    });
    graphData.links.forEach((l) => {
      if (degrees[l.source] !== undefined) degrees[l.source]++;
      if (degrees[l.target] !== undefined) degrees[l.target]++;
    });

    const width = 800;
    const height = 600;

    // Map raw nodes
    const parsedNodes: Node[] = graphData.nodes.map((n, index) => {
      // Circle layout to distribute nodes
      const angle = (index / graphData.nodes.length) * 2 * Math.PI;
      const radius = 220 + Math.random() * 80;
      
      return {
        id: n.id,
        label: n.label || n.id,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        community: typeof n.community === "number" ? n.community : 9,
        file_type: n.file_type || "concept",
        degree: degrees[n.id] || 0,
      };
    });

    // Map links
    const parsedLinks: Link[] = graphData.links.map((l) => ({
      source: l.source,
      target: l.target,
      relation: l.relation || "connected",
      confidence: l.confidence || "EXTRACTED",
    }));

    // Hyperedges
    const parsedHyperedges = graphData.graph?.hyperedges || [];

    return { initialNodes: parsedNodes, initialLinks: parsedLinks, hyperedges: parsedHyperedges };
  }, [graphData]);

  const [nodes, setNodes] = useState<Node[]>([]);
  const nodesRef = useRef<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [simTicks, setSimTicks] = useState(0);
  const [isSimulationRunning, setIsSimulationRunning] = useState(true);

  // Initialize nodes
  useEffect(() => {
    if (initialNodes.length > 0) {
      setNodes(initialNodes);
      nodesRef.current = initialNodes;
      setLinks(initialLinks);
      setSimTicks(0);
      setIsSimulationRunning(true);
    }
  }, [initialNodes, initialLinks]);

  // Verlet integration with stabilization
  useEffect(() => {
    if (nodes.length === 0 || !isSimulationRunning) return;

    let animFrameId: number;
    const maxTicks = 180; // Stop physics after 180 frames (stabilization)
    
    const kRepulsion = 2600;
    const kAttraction = 0.045;
    const restLength = 85;
    const kGravity = 0.025;
    const damping = 0.8;
    const width = 800;
    const height = 600;

    const tick = () => {
      const currentNodes = [...nodesRef.current];
      if (currentNodes.length === 0) return;

      const nodeMap = new Map<string, Node>();
      currentNodes.forEach((n) => nodeMap.set(n.id, n));

      // 1. Repulsion
      for (let i = 0; i < currentNodes.length; i++) {
        const n1 = currentNodes[i];
        if (hiddenCommunities.has(n1.community)) continue;

        for (let j = i + 1; j < currentNodes.length; j++) {
          const n2 = currentNodes[j];
          if (hiddenCommunities.has(n2.community)) continue;

          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const distSq = dx * dx + dy * dy + 1;
          const dist = Math.sqrt(distSq);

          if (dist < 280) {
            const force = (kRepulsion / distSq) * (dist < 35 ? 4 : 1);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }
        }
      }

      // 2. Attraction
      initialLinks.forEach((link) => {
        const sNode = nodeMap.get(link.source);
        const tNode = nodeMap.get(link.target);
        if (sNode && tNode) {
          if (hiddenCommunities.has(sNode.community) || hiddenCommunities.has(tNode.community)) return;

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

      // 4. Update coordinates
      let totalVelocity = 0;
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
          
          const speed = Math.sqrt(vx * vx + vy * vy);
          if (speed > 12) {
            vx = (vx / speed) * 12;
            vy = (vy / speed) * 12;
          }

          totalVelocity += Math.abs(vx) + Math.abs(vy);

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

      setSimTicks((prev) => {
        const next = prev + 1;
        // Stop physics if maximum iterations reached, or nodes have stopped moving (stabilized)
        if (next >= maxTicks || totalVelocity < 0.8) {
          setIsSimulationRunning(false);
          return next;
        }
        return next;
      });

      if (simTicks < maxTicks && totalVelocity >= 0.8) {
        animFrameId = requestAnimationFrame(tick);
      }
    };

    animFrameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameId);
  }, [initialLinks, isSimulationRunning, simTicks, hiddenCommunities, nodes.length]);

  // Wake up physics on action (e.g. node drag or community filter toggle)
  const wakeSimulation = () => {
    setSimTicks(0);
    setIsSimulationRunning(true);
  };

  // Pan canvas
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
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
      const svg = svgRef.current;
      if (!svg) return;

      const rect = svg.getBoundingClientRect();
      const mX = e.clientX - rect.left;
      const mY = e.clientY - rect.top;

      const graphX = (mX - transform.x) / transform.k;
      const graphY = (mY - transform.y) / transform.k;

      nodesRef.current = nodesRef.current.map((n) => {
        if (n.id === draggedNodeId) {
          return { ...n, fx: graphX, fy: graphY, x: graphX, y: graphY };
        }
        return n;
      });
      wakeSimulation();
    }
  };

  const handleMouseUp = () => {
    setIsDraggingCanvas(false);
    if (draggedNodeId) {
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

  const handleWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const svg = svgRef.current;
    if (!svg) return;

    const rect = svg.getBoundingClientRect();
    const mX = e.clientX - rect.left;
    const mY = e.clientY - rect.top;

    const zoomFactor = 1.05;
    const nextK = e.deltaY < 0 ? transform.k * zoomFactor : transform.k / zoomFactor;
    const k = Math.max(0.15, Math.min(4, nextK));

    const dx = mX - transform.x;
    const dy = mY - transform.y;
    const x = mX - dx * (k / transform.k);
    const y = mY - dy * (k / transform.k);

    setTransform({ x, y, k });
  };

  // Node focus helper
  const focusNode = (nodeId: string) => {
    const node = nodes.find((n) => n.id === nodeId);
    if (!node || !svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    // Zoom scale to 1.3
    const scale = 1.2;
    // Translate node position to the center of the canvas viewport
    const x = width / 2 - node.x * scale;
    const y = height / 2 - node.y * scale;

    setTransform({ x, y, k: scale });
    setSelectedNodeId(nodeId);
    setSearchQuery("");
    setShowSuggestions(false);
  };

  // Autocomplete search matching
  const searchMatches = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase().trim();
    return nodes
      .filter((n) => !hiddenCommunities.has(n.community) && n.label.toLowerCase().includes(q))
      .slice(0, 10);
  }, [searchQuery, nodes, hiddenCommunities]);

  // Selected Node Details
  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  const selectedNodeMetadata = useMemo(() => {
    if (!selectedNodeId || !graphData) return null;
    return graphData.nodes.find((n) => n.id === selectedNodeId) || null;
  }, [selectedNodeId, graphData]);

  // Node neighbors lookup
  const selectedNodeNeighbors = useMemo(() => {
    if (!selectedNodeId) return [];
    const ids = new Set<string>();
    
    links.forEach((l) => {
      if (l.source === selectedNodeId) ids.add(l.target);
      if (l.target === selectedNodeId) ids.add(l.source);
    });

    return nodes
      .filter((n) => ids.has(n.id) && !hiddenCommunities.has(n.community))
      .slice(0, 15);
  }, [selectedNodeId, links, nodes, hiddenCommunities]);

  // List of connected node IDs (hover highlighting)
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

  // Communities list with counts
  const communities = useMemo(() => {
    const counts: Record<number, number> = {};
    nodes.forEach((n) => {
      counts[n.community] = (counts[n.community] || 0) + 1;
    });

    return Object.keys(counts)
      .map((cidStr) => {
        const cid = parseInt(cidStr, 10);
        return {
          id: cid,
          name: COMMUNITY_NAMES[cid] || `Community ${cid}`,
          color: COMMUNITY_COLORS[cid % COMMUNITY_COLORS.length],
          count: counts[cid],
        };
      })
      .sort((a, b) => b.count - a.count);
  }, [nodes]);

  // Toggle community visibility
  const toggleCommunity = (cid: number) => {
    const next = new Set(hiddenCommunities);
    if (next.has(cid)) {
      next.delete(cid);
    } else {
      next.add(cid);
      if (selectedNode?.community === cid) {
        setSelectedNodeId(null);
      }
    }
    setHiddenCommunities(next);
    wakeSimulation();
  };

  const toggleAllCommunities = (checked: boolean) => {
    if (checked) {
      setHiddenCommunities(new Set());
    } else {
      setHiddenCommunities(new Set(communities.map((c) => c.id)));
      setSelectedNodeId(null);
    }
    wakeSimulation();
  };

  // Filter links for visible nodes
  const visibleLinks = useMemo(() => {
    return links.filter(
      (l) => !hiddenCommunities.has(nodes.find((n) => n.id === l.source)?.community ?? -1) &&
             !hiddenCommunities.has(nodes.find((n) => n.id === l.target)?.community ?? -1)
    );
  }, [links, nodes, hiddenCommunities]);

  // Filter nodes
  const visibleNodes = useMemo(() => {
    return nodes.filter((n) => !hiddenCommunities.has(n.community));
  }, [nodes, hiddenCommunities]);

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalContainer} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <header className={styles.modalHeader}>
          <div className={styles.modalBrand}>
            <span className={styles.modalTitle}>WDB Knowledge Graph Explorer</span>
            <span className={styles.modalSubtitle}>
              Interactive network visualization of WDB initiatives & concepts
            </span>
          </div>
          <button className={styles.modalCloseBtn} onClick={onClose} aria-label="Close explorer">
            ✕
          </button>
        </header>

        <div className={styles.modalMain}>
          {/* Main Visualizer Area */}
          <div className={styles.modalGraphWrap}>
            <svg
              ref={svgRef}
              className={styles.modalSvg}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
            >
              {/* Grid backdrop */}
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" pointerEvents="all" />

              <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
                {/* Hyperedges (shaded boundary circles/regions if available) */}
                {hyperedges.map((h, i) => {
                  const positions = h.nodes
                    .map((nid: string) => nodes.find((n) => n.id === nid))
                    .filter((n: any) => n !== undefined && !hiddenCommunities.has(n.community));

                  if (positions.length < 2) return null;

                  // Find centroid and radius to draw hyperedge bounds
                  const cx = positions.reduce((s: number, p: any) => s + p.x, 0) / positions.length;
                  const cy = positions.reduce((s: number, p: any) => s + p.y, 0) / positions.length;
                  
                  // Compute max distance from centroid
                  let maxR = 40;
                  positions.forEach((p: any) => {
                    const dx = p.x - cx;
                    const dy = p.y - cy;
                    const d = Math.sqrt(dx * dx + dy * dy);
                    if (d > maxR) maxR = d;
                  });

                  return (
                    <g key={`hyperedge-${h.id}-${i}`}>
                      <circle
                        cx={cx}
                        cy={cy}
                        r={maxR * 1.2}
                        className={styles.hyperedgeRegion}
                      />
                      <text
                        x={cx}
                        y={cy - maxR * 1.2 - 6}
                        fill="rgba(99, 102, 241, 0.6)"
                        fontSize="9"
                        fontWeight="bold"
                        textAnchor="middle"
                        pointerEvents="none"
                      >
                        {h.label}
                      </text>
                    </g>
                  );
                })}

                {/* Edges */}
                {visibleLinks.map((link, i) => {
                  const sNode = nodes.find((n) => n.id === link.source);
                  const tNode = nodes.find((n) => n.id === link.target);
                  if (!sNode || !tNode) return null;

                  const isActive =
                    connectedNodeIds &&
                    connectedNodeIds.has(link.source) &&
                    connectedNodeIds.has(link.target);

                  return (
                    <line
                      key={`global-edge-${link.source}-${link.target}-${i}`}
                      x1={sNode.x}
                      y1={sNode.y}
                      x2={tNode.x}
                      y2={tNode.y}
                      className={`${styles.modalLink} ${isActive ? styles.active : ""}`}
                      strokeDasharray={link.confidence === "INFERRED" ? "3,3" : undefined}
                    />
                  );
                })}

                {/* Nodes */}
                {visibleNodes.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  const isHovered = hoveredNodeId === node.id;
                  const isDimmed = connectedNodeIds && !connectedNodeIds.has(node.id);

                  // Compute sizing based on node degree
                  const r = 5 + Math.min(node.degree * 1.5, 12);
                  const color = COMMUNITY_COLORS[node.community % COMMUNITY_COLORS.length];

                  return (
                    <g
                      key={`global-node-${node.id}`}
                      className={`${styles.nodeGroup} ${isSelected ? styles.nodeSelected : ""} ${
                        isHovered ? styles.nodeHover : ""
                      } ${isDimmed ? styles.nodeDimmed : ""}`}
                      transform={`translate(${node.x}, ${node.y})`}
                      onMouseEnter={() => setHoveredNodeId(node.id)}
                      onMouseLeave={() => setHoveredNodeId(null)}
                      onMouseDown={(e) => {
                        e.stopPropagation();
                        setDraggedNodeId(node.id);
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNodeId(node.id);
                      }}
                    >
                      {isSelected && (
                        <circle
                          r={r + 5}
                          fill="none"
                          stroke="var(--wf-accent)"
                          strokeWidth={1.5}
                          className={styles.pulse}
                        />
                      )}
                      <circle
                        r={r}
                        fill={color}
                        className={styles.modalNodeCircle}
                      />
                      
                      {/* Node text label (always show if selected/hovered or if node is highly connected) */}
                      {(isSelected || isHovered || (transform.k > 0.6 && node.degree > 4) || transform.k > 1) && (
                        <text
                          y={r + 13}
                          textAnchor="middle"
                          fill="var(--wf-text-slate-200)"
                          fontSize="9"
                          fontWeight={node.degree > 6 ? "700" : "500"}
                          style={{
                            paintOrder: "stroke",
                            stroke: "var(--wf-surface-deep)",
                            strokeWidth: 3,
                            strokeLinecap: "round",
                            strokeLinejoin: "round",
                            pointerEvents: "none"
                          }}
                        >
                          {node.label}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </svg>

            {/* View navigation buttons */}
            <div className={styles.globalControls}>
              <button onClick={() => setTransform((prev) => ({ ...prev, k: Math.min(4, prev.k * 1.2) }))} title="Zoom In">+</button>
              <button onClick={() => setTransform((prev) => ({ ...prev, k: Math.max(0.15, prev.k / 1.2) }))} title="Zoom Out">-</button>
              <button onClick={() => setTransform({ x: 120, y: 100, k: 0.6 })} title="Reset View">⟲</button>
            </div>
          </div>

          {/* Right Sidebar Control Panel */}
          <div className={styles.modalSidebar}>
            {/* Search autocomplete input */}
            <div className={styles.searchSection}>
              <input
                type="text"
                placeholder="Search nodes..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              />
              {showSuggestions && searchMatches.length > 0 && (
                <div className={styles.searchResultsList}>
                  {searchMatches.map((m) => (
                    <div
                      key={m.id}
                      className={styles.searchResultItem}
                      onMouseDown={() => focusNode(m.id)}
                    >
                      {m.label}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Node Info Inspector */}
            <div className={styles.infoSection}>
              <h3>Node Info</h3>
              {!selectedNode ? (
                <div className={styles.emptyInfo}>Click a node to inspect it</div>
              ) : (
                <div className={styles.infoContent}>
                  <div className={styles.nodeName}>{selectedNode.label}</div>
                  <div className={styles.infoField}>
                    <strong>Type:</strong>{" "}
                    <span
                      className={styles.infoBadge}
                      style={{
                        backgroundColor: `${COMMUNITY_COLORS[selectedNode.community % COMMUNITY_COLORS.length]}22`,
                        color: COMMUNITY_COLORS[selectedNode.community % COMMUNITY_COLORS.length],
                      }}
                    >
                      {selectedNodeMetadata?.file_type || "concept"}
                    </span>
                  </div>
                  <div className={styles.infoField}>
                    <strong>Community:</strong>{" "}
                    {COMMUNITY_NAMES[selectedNode.community] || `Community ${selectedNode.community}`}
                  </div>
                  <div className={styles.infoField}>
                    <strong>Degree:</strong> {selectedNode.degree} connections
                  </div>
                  {selectedNodeMetadata?.source_file && (
                    <div className={styles.infoField}>
                      <strong>Source file:</strong>{" "}
                      <span
                        className={styles.viewDocLink}
                        onClick={() => openSource(selectedNodeMetadata.source_file)}
                      >
                        Open Note
                      </span>
                    </div>
                  )}
                  {/* Neighbors list */}
                  {selectedNodeNeighbors.length > 0 && (
                    <div className={styles.neighborField}>
                      <strong>Neighbors ({selectedNodeNeighbors.length}):</strong>
                      <div className={styles.neighborsList}>
                        {selectedNodeNeighbors.map((nb) => (
                          <span
                            key={nb.id}
                            className={styles.neighborLink}
                            style={{ borderLeftColor: COMMUNITY_COLORS[nb.community % COMMUNITY_COLORS.length] }}
                            onClick={() => focusNode(nb.id)}
                          >
                            {nb.label}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Community visibility control list */}
            <div className={styles.legendSection}>
              <h3>Initiatives / Communities</h3>
              <div className={styles.legendControls}>
                <label>
                  <input
                    type="checkbox"
                    className={styles.customCheckbox}
                    checked={hiddenCommunities.size === 0}
                    ref={(el) => {
                      if (el) {
                        el.indeterminate =
                          hiddenCommunities.size > 0 && hiddenCommunities.size < communities.length;
                      }
                    }}
                    onChange={(e) => toggleAllCommunities(e.target.checked)}
                  />
                  <span>Select All</span>
                </label>
              </div>
              <div className={styles.legendCheckList}>
                {communities.map((c) => {
                  const isChecked = !hiddenCommunities.has(c.id);
                  return (
                    <div
                      key={c.id}
                      className={`${styles.legendItem} ${!isChecked ? styles.dimmed : ""}`}
                      onClick={() => toggleCommunity(c.id)}
                    >
                      <input
                        type="checkbox"
                        className={styles.customCheckbox}
                        checked={isChecked}
                        onChange={() => {}} // handled by legendItem click
                      />
                      <div className={styles.legendDot} style={{ backgroundColor: c.color }} />
                      <span className={styles.legendLabel} title={c.name}>
                        {c.name}
                      </span>
                      <span className={styles.legendCount}>{c.count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Stats Footer */}
            <div className={styles.statsSection}>
              {visibleNodes.length} nodes &middot; {visibleLinks.length} edges &middot; {communities.length} communities
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
