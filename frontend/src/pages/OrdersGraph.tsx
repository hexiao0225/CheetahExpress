import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowLeft, Share2 } from "lucide-react";
import { orderApi } from "../utils/api";

export default function OrdersGraph() {
  const { data, isLoading } = useQuery({
    queryKey: ["ordersGraph"],
    queryFn: () => orderApi.getOrdersGraph().then((res) => res.data),
    refetchInterval: 10000,
  });

  const graphRows = data?.orders || [];
  const orderIds = useMemo(
    () => Array.from(new Set(graphRows.map((row) => row.order_id))),
    [graphRows],
  );

  const driverNames = useMemo(
    () =>
      Array.from(
        new Set((data?.drivers || []).map((driver) => driver.driver_name)),
      ),
    [data?.drivers],
  );

  const [orderNodePositions, setOrderNodePositions] = useState<
    Record<string, { x: number; y: number }>
  >({});
  const [driverNodePositions, setDriverNodePositions] = useState<
    Record<string, { x: number; y: number }>
  >({});
  const [draggingNode, setDraggingNode] = useState<{
    type: "order" | "driver";
    id: string;
  } | null>(null);

  const graphHeight = Math.max(
    300,
    140 + Math.max(orderIds.length, driverNames.length) * 58,
  );
  const orderX = 180;
  const driverX = 650;

  useEffect(() => {
    setOrderNodePositions((prev) => {
      const next = { ...prev };
      orderIds.forEach((orderId, idx) => {
        if (!next[orderId]) {
          next[orderId] = { x: orderX, y: 90 + idx * 58 };
        }
      });
      Object.keys(next).forEach((id) => {
        if (!orderIds.includes(id)) {
          delete next[id];
        }
      });
      return next;
    });
  }, [orderIds]);

  useEffect(() => {
    setDriverNodePositions((prev) => {
      const next = { ...prev };
      driverNames.forEach((driverName, idx) => {
        if (!next[driverName]) {
          next[driverName] = { x: driverX, y: 90 + idx * 58 };
        }
      });
      Object.keys(next).forEach((id) => {
        if (!driverNames.includes(id)) {
          delete next[id];
        }
      });
      return next;
    });
  }, [driverNames]);

  const orderNodeMap = new Map(
    orderIds.map((orderId, idx) => [
      orderId,
      orderNodePositions[orderId] || { x: orderX, y: 90 + idx * 58 },
    ]),
  );
  const driverNodeMap = new Map(
    driverNames.map((driverName, idx) => [
      driverName,
      driverNodePositions[driverName] || { x: driverX, y: 90 + idx * 58 },
    ]),
  );

  const handleGraphMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!draggingNode) {
      return;
    }
    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 860;
    const y = ((event.clientY - rect.top) / rect.height) * graphHeight;

    const clampedY = Math.min(graphHeight - 35, Math.max(35, y));

    if (draggingNode.type === "order") {
      setOrderNodePositions((prev) => ({
        ...prev,
        [draggingNode.id]: {
          x: Math.min(310, Math.max(120, x)),
          y: clampedY,
        },
      }));
      return;
    }

    setDriverNodePositions((prev) => ({
      ...prev,
      [draggingNode.id]: {
        x: Math.min(760, Math.max(520, x)),
        y: clampedY,
      },
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cheetah-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            to="/orders"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              All Orders Graph
            </h1>
            <p className="text-gray-600 mt-1">
              Neo4j relationships across orders and assigned drivers
            </p>
          </div>
        </div>
        <div className="text-sm text-gray-600">
          {orderIds.length} orders · {driverNames.length} drivers
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl shadow-sm border border-slate-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Share2 className="h-6 w-6 text-cyan-300" />
          <h2 className="text-lg font-semibold text-white">
            Orders ↔ Drivers Neo4j Graph
          </h2>
        </div>

        <div className="w-full overflow-x-auto border border-slate-700 rounded-lg bg-slate-950/60">
          <svg
            viewBox={`0 0 860 ${graphHeight}`}
            className="w-full min-w-[860px] h-auto"
            onMouseMove={handleGraphMouseMove}
            onMouseUp={() => setDraggingNode(null)}
            onMouseLeave={() => setDraggingNode(null)}
          >
            <defs>
              <marker
                id="arrow-all-orders"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" />
              </marker>
            </defs>

            {graphRows
              .filter((row) => row.driver_name)
              .map((row, idx) => {
                const from = orderNodeMap.get(row.order_id);
                const to = driverNodeMap.get(row.driver_name || "");
                if (!from || !to) {
                  return null;
                }
                const midX = (from.x + to.x) / 2;
                return (
                  <g key={`${row.order_id}-${row.driver_name}-${idx}`}>
                    <path
                      d={`M ${from.x + 120} ${from.y} C ${midX} ${from.y}, ${midX} ${to.y}, ${to.x - 120} ${to.y}`}
                      stroke="#38bdf8"
                      strokeWidth="2"
                      fill="none"
                      markerEnd="url(#arrow-all-orders)"
                      opacity="0.9"
                    />
                    <text
                      x={midX}
                      y={(from.y + to.y) / 2 - 5}
                      textAnchor="middle"
                      fontSize="10"
                      fill="#bae6fd"
                    >
                      ASSIGNED_TO
                    </text>
                  </g>
                );
              })}

            {orderIds.map((orderId) => {
              const node = orderNodeMap.get(orderId);
              if (!node) {
                return null;
              }
              return (
                <g
                  key={orderId}
                  onMouseDown={() =>
                    setDraggingNode({ type: "order", id: orderId })
                  }
                  style={{
                    cursor:
                      draggingNode?.type === "order" &&
                      draggingNode.id === orderId
                        ? "grabbing"
                        : "grab",
                  }}
                >
                  <rect
                    x={node.x - 120}
                    y={node.y - 20}
                    width="240"
                    height="42"
                    rx="10"
                    fill="#fb923c"
                    opacity="0.95"
                  />
                  <text
                    x={node.x}
                    y={node.y + 1}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize="12"
                    fill="#ffffff"
                    fontWeight="700"
                  >
                    Order {orderId}
                  </text>
                </g>
              );
            })}

            {driverNames.map((driverName) => {
              const node = driverNodeMap.get(driverName);
              if (!node) {
                return null;
              }
              const hasAssignment = graphRows.some(
                (row) => row.driver_name === driverName,
              );
              return (
                <g
                  key={driverName}
                  onMouseDown={() =>
                    setDraggingNode({ type: "driver", id: driverName })
                  }
                  style={{
                    cursor:
                      draggingNode?.type === "driver" &&
                      draggingNode.id === driverName
                        ? "grabbing"
                        : "grab",
                  }}
                >
                  <rect
                    x={node.x - 120}
                    y={node.y - 20}
                    width="240"
                    height="42"
                    rx="10"
                    fill={hasAssignment ? "#0f766e" : "#334155"}
                    opacity="0.95"
                  />
                  <text
                    x={node.x}
                    y={node.y + 1}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize="12"
                    fill="#ffffff"
                    fontWeight="700"
                  >
                    {driverName}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </div>
  );
}
