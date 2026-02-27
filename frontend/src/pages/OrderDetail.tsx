import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Package,
  User,
  Phone,
  CheckCircle2,
  XCircle,
  MapPin,
  Share2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { orderApi } from "../utils/api";
import { motion } from "framer-motion";
import DriverMap from "../components/DriverMap";

const haversineKm = (
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
) => {
  const toRad = (v: number) => (v * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

export default function OrderDetail() {
  const { orderId } = useParams<{ orderId: string }>();

  const { data: audit, isLoading } = useQuery({
    queryKey: ["orderAudit", orderId],
    queryFn: () => orderApi.getAuditTrail(orderId!).then((res) => res.data),
    enabled: !!orderId,
    refetchInterval: 5000, // Refresh every 5 seconds for live GPS tracking
  });

  const graphOrderId = audit?.order_id || orderId || "ORDER";
  const graphDriverIds = Array.from(
    new Set(
      [
        ...(audit?.compliance_checks?.map((c: any) => c.driver_id) || []),
        ...(audit?.rankings?.map((r: any) => r.driver_id) || []),
        ...(audit?.voice_calls?.map((c: any) => c.driver_id) || []),
        ...(audit?.assignments?.map((a: any) => a.driver_id) || []),
      ].filter(Boolean),
    ),
  );

  const graphHeight = Math.max(260, 100 + graphDriverIds.length * 56);
  const graphOrderX = 140;
  const graphDriverX = 520;

  const [driverNodePositions, setDriverNodePositions] = useState<
    Record<string, { x: number; y: number }>
  >({});
  const [draggingDriverId, setDraggingDriverId] = useState<string | null>(null);

  useEffect(() => {
    setDriverNodePositions((prev) => {
      const next = { ...prev };
      graphDriverIds.forEach((driverId, idx) => {
        if (!next[driverId]) {
          next[driverId] = { x: graphDriverX, y: 80 + idx * 56 };
        }
      });
      Object.keys(next).forEach((driverId) => {
        if (!graphDriverIds.includes(driverId)) {
          delete next[driverId];
        }
      });
      return next;
    });
  }, [graphDriverIds, graphDriverX]);

  const pickupLat = Number(audit?.order_details?.pickup_latitude);
  const pickupLng = Number(audit?.order_details?.pickup_longitude);
  const dropoffLat = Number(audit?.order_details?.dropoff_latitude);
  const dropoffLng = Number(audit?.order_details?.dropoff_longitude);

  const hasDriverGeo =
    audit?.driver_location &&
    Number.isFinite(pickupLat) &&
    Number.isFinite(pickupLng);

  const driverToPickupGeoKm = hasDriverGeo
    ? haversineKm(
        audit!.driver_location!.latitude,
        audit!.driver_location!.longitude,
        pickupLat,
        pickupLng,
      )
    : null;

  const pickupToDropoffGeoKm =
    Number.isFinite(pickupLat) &&
    Number.isFinite(pickupLng) &&
    Number.isFinite(dropoffLat) &&
    Number.isFinite(dropoffLng)
      ? haversineKm(pickupLat, pickupLng, dropoffLat, dropoffLng)
      : null;

  const driverNodeMap = new Map<string, { x: number; y: number }>(
    graphDriverIds.map((driverId, idx) => [
      driverId,
      driverNodePositions[driverId] || { x: graphDriverX, y: 80 + idx * 56 },
    ]),
  );

  const complianceByDriver = new Map<string, boolean>(
    (audit?.compliance_checks || []).map((check: any) => [
      check.driver_id,
      !!check.is_compliant,
    ]),
  );
  const rankByDriver = new Map<string, number>(
    (audit?.rankings || []).map((ranking: any) => [
      ranking.driver_id,
      ranking.rank,
    ]),
  );
  const callOutcomeByDriver = new Map<string, string>(
    (audit?.voice_calls || []).map((call: any) => [
      call.driver_id,
      call.outcome || "unknown",
    ]),
  );
  const assignedDriverSet = new Set<string>(
    (audit?.assignments || []).map((assignment: any) => assignment.driver_id),
  );

  const graphEdges: Array<{
    from: { x: number; y: number };
    to: { x: number; y: number };
    label: string;
    color: string;
  }> = [];

  (audit?.compliance_checks || []).forEach((check: any) => {
    const node = driverNodeMap.get(check.driver_id);
    if (node) {
      graphEdges.push({
        from: { x: graphOrderX + 90, y: graphHeight / 2 },
        to: { x: node.x - 90, y: node.y },
        label: "CHECK",
        color: check.is_compliant ? "#16a34a" : "#dc2626",
      });
    }
  });

  (audit?.rankings || []).forEach((ranking: any) => {
    const node = driverNodeMap.get(ranking.driver_id);
    if (node) {
      graphEdges.push({
        from: { x: graphOrderX + 90, y: graphHeight / 2 },
        to: { x: node.x - 90, y: node.y },
        label: `RANK #${ranking.rank}`,
        color: "#f97316",
      });
    }
  });

  (audit?.voice_calls || []).forEach((call: any) => {
    const node = driverNodeMap.get(call.driver_id);
    if (node) {
      graphEdges.push({
        from: { x: graphOrderX + 90, y: graphHeight / 2 },
        to: { x: node.x - 90, y: node.y },
        label: `CALLED (${call.outcome || "unknown"})`,
        color: "#6366f1",
      });
    }
  });

  (audit?.assignments || []).forEach((assignment: any) => {
    const node = driverNodeMap.get(assignment.driver_id);
    if (node) {
      graphEdges.push({
        from: { x: node.x - 90, y: node.y },
        to: { x: graphOrderX + 90, y: graphHeight / 2 },
        label: "ASSIGNED_TO",
        color: "#0ea5e9",
      });
    }
  });

  const handleGraphMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!draggingDriverId) {
      return;
    }
    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 760;
    const y = ((event.clientY - rect.top) / rect.height) * graphHeight;
    setDriverNodePositions((prev) => ({
      ...prev,
      [draggingDriverId]: {
        x: Math.min(670, Math.max(420, x)),
        y: Math.min(graphHeight - 35, Math.max(35, y)),
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
      <div className="flex items-center gap-4">
        <Link
          to="/orders"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Order Details</h1>
          <p className="text-gray-600 mt-1">{orderId}</p>
        </div>
      </div>

      {/* Order Info */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Package className="h-6 w-6 text-cheetah-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            Order Information
          </h2>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium text-gray-900">
              {audit?.order_details?.status || "Processing"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Vehicle Type</p>
            <p className="font-medium text-gray-900">
              {audit?.order_details?.vehicle_type || "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Checks */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Compliance Checks
        </h2>
        <div className="space-y-3">
          {audit?.compliance_checks?.map((check: any, index: number) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                {check.is_compliant ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
                <div>
                  <p className="font-medium text-gray-900">
                    Driver {check.driver_id}
                  </p>
                  <p className="text-sm text-gray-600">
                    {check.reasons?.[0] || "All checks passed"}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Rankings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Driver Rankings
        </h2>
        <div className="space-y-3">
          {audit?.rankings?.map((ranking: any, index: number) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-cheetah-100 flex items-center justify-center font-bold text-cheetah-600">
                  #{ranking.rank}
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    Driver {ranking.driver_id}
                  </p>
                  <p className="text-sm text-gray-600">
                    Score: {ranking.score?.toFixed(2)}
                  </p>
                </div>
              </div>
              <span className="text-sm text-gray-500">
                {ranking.eta_minutes?.toFixed(0)} min ETA
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Neo4j Graph */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl shadow-sm border border-slate-700 p-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <Share2 className="h-6 w-6 text-cyan-300" />
          <h2 className="text-lg font-semibold text-white">
            Neo4j Decision Graph
          </h2>
        </div>
        <div className="flex flex-wrap gap-2 text-xs mb-4">
          <span className="px-2 py-1 rounded bg-green-500/20 text-green-200 border border-green-500/40">
            COMPLIANCE
          </span>
          <span className="px-2 py-1 rounded bg-orange-500/20 text-orange-200 border border-orange-500/40">
            RANK
          </span>
          <span className="px-2 py-1 rounded bg-indigo-500/20 text-indigo-200 border border-indigo-500/40">
            CALLED
          </span>
          <span className="px-2 py-1 rounded bg-sky-500/20 text-sky-200 border border-sky-500/40">
            ASSIGNED_TO
          </span>
        </div>
        <div className="w-full overflow-x-auto border border-slate-700 rounded-lg bg-slate-950/60">
          <svg
            viewBox={`0 0 760 ${graphHeight}`}
            className="w-full min-w-[760px] h-auto"
            onMouseMove={handleGraphMouseMove}
            onMouseUp={() => setDraggingDriverId(null)}
            onMouseLeave={() => setDraggingDriverId(null)}
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
              </marker>
              <filter
                id="node-glow"
                x="-50%"
                y="-50%"
                width="200%"
                height="200%"
              >
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {graphEdges.map((edge, idx) => {
              const midX = (edge.from.x + edge.to.x) / 2;
              const midY = (edge.from.y + edge.to.y) / 2;
              return (
                <g key={`${edge.label}-${idx}`}>
                  <path
                    d={`M ${edge.from.x} ${edge.from.y} C ${midX} ${edge.from.y}, ${midX} ${edge.to.y}, ${edge.to.x} ${edge.to.y}`}
                    stroke={edge.color}
                    strokeWidth="2"
                    fill="none"
                    markerEnd="url(#arrow)"
                    opacity="0.9"
                  />
                  <text
                    x={midX}
                    y={midY - 4}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#cbd5e1"
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}

            <rect
              x={graphOrderX - 90}
              y={graphHeight / 2 - 26}
              width="180"
              height="52"
              rx="12"
              fill="#fb923c"
              opacity="0.95"
              filter="url(#node-glow)"
            />
            <text
              x={graphOrderX}
              y={graphHeight / 2}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="12"
              fill="#ffffff"
              fontWeight="700"
            >
              Order {graphOrderId}
            </text>

            {graphDriverIds.map((driverId, idx) => {
              const node = driverNodeMap.get(driverId) || {
                x: graphDriverX,
                y: 80 + idx * 56,
              };
              const compliance = complianceByDriver.get(driverId);
              const rank = rankByDriver.get(driverId);
              const callOutcome = callOutcomeByDriver.get(driverId);
              const isAssigned = assignedDriverSet.has(driverId);
              return (
                <g
                  key={driverId}
                  onMouseDown={() => setDraggingDriverId(driverId)}
                  style={{
                    cursor: draggingDriverId === driverId ? "grabbing" : "grab",
                  }}
                >
                  <rect
                    x={node.x - 110}
                    y={node.y - 26}
                    width="220"
                    height="58"
                    rx="12"
                    fill={isAssigned ? "#0f766e" : "#1e293b"}
                    opacity="0.98"
                    filter="url(#node-glow)"
                  />
                  <text
                    x={node.x}
                    y={node.y - 8}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize="12"
                    fill="#ffffff"
                    fontWeight="700"
                  >
                    Driver {driverId} {isAssigned ? "★" : ""}
                  </text>
                  <text
                    x={node.x}
                    y={node.y + 12}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontSize="10"
                    fill="#cbd5e1"
                  >
                    C:
                    {compliance === undefined
                      ? "-"
                      : compliance
                        ? "✅"
                        : "❌"}{" "}
                    · R:
                    {rank ?? "-"} · Call:{callOutcome ?? "-"}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </motion.div>

      {/* Voice Calls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <Phone className="h-6 w-6 text-cheetah-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            Voice Call History
          </h2>
        </div>
        <div className="space-y-3">
          {audit?.voice_calls?.map((call: any, index: number) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <User className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="font-medium text-gray-900">
                    Driver {call.driver_id}
                  </p>
                  <div className="flex items-center gap-4 mt-1">
                    <span
                      className={`text-sm px-2 py-1 rounded ${
                        call.outcome === "accepted"
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {call.outcome}
                    </span>
                    {call.sentiment && (
                      <span className="text-sm text-gray-600">
                        Sentiment: {(call.sentiment * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {call.decline_reason && (
                    <p className="text-sm text-red-600 mt-1">
                      {call.decline_reason}
                    </p>
                  )}
                  {call.transcript && (
                    <div className="mt-2 p-3 bg-white border border-gray-200 rounded-md">
                      <p className="text-xs font-semibold text-gray-500 mb-1">
                        Transcript
                      </p>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {call.transcript}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Assignment */}
      {audit?.assignments && audit.assignments.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white"
        >
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle2 className="h-6 w-6" />
            <h2 className="text-lg font-semibold">Assignment Confirmed</h2>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm opacity-90">Driver ID</p>
              <p className="font-bold">{audit.assignments[0].driver_id}</p>
            </div>
            <div>
              <p className="text-sm opacity-90">Distance</p>
              <p className="font-bold">
                {audit.assignments[0].distance_km?.toFixed(1)} km
              </p>
            </div>
            <div>
              <p className="text-sm opacity-90">Duration</p>
              <p className="font-bold">
                {(audit.assignments[0].duration_hours * 60).toFixed(0)} min
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Live GPS Tracking */}
      {audit?.driver_location && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <MapPin className="h-6 w-6 text-cheetah-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Live Driver GPS Tracking
            </h2>
          </div>
          <div className="mb-4 grid md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                Driver Details
              </p>
              <p className="text-sm text-gray-700">
                Name:{" "}
                <span className="font-semibold text-gray-900">
                  {audit.driver_location.name}
                </span>
              </p>
              <p className="text-sm text-gray-700">
                Phone:{" "}
                <span className="font-semibold text-gray-900">
                  {audit.driver_location.phone}
                </span>
              </p>
              <p className="text-sm text-gray-700">
                Vehicle:{" "}
                <span className="font-semibold text-gray-900">
                  {audit.driver_location.vehicle_type || "N/A"}
                </span>
              </p>
              <p className="text-sm text-gray-700">
                License:{" "}
                <span className="font-semibold text-gray-900">
                  {audit.driver_location.license_number || "N/A"}
                </span>
              </p>
            </div>
            <div className="p-4 rounded-lg bg-cheetah-50 border border-cheetah-200">
              <p className="text-xs text-cheetah-700 uppercase tracking-wide mb-2">
                GEO Distance Metrics
              </p>
              <p className="text-sm text-gray-700">
                Driver → Pickup:{" "}
                <span className="font-semibold text-gray-900">
                  {driverToPickupGeoKm !== null
                    ? `${driverToPickupGeoKm.toFixed(2)} km`
                    : "N/A"}
                </span>
              </p>
              <p className="text-sm text-gray-700">
                Pickup → Dropoff:{" "}
                <span className="font-semibold text-gray-900">
                  {pickupToDropoffGeoKm !== null
                    ? `${pickupToDropoffGeoKm.toFixed(2)} km`
                    : "N/A"}
                </span>
              </p>
              <p className="text-sm text-gray-700">
                Route Distance (assigned):{" "}
                <span className="font-semibold text-gray-900">
                  {audit.assignments?.[0]?.distance_km
                    ? `${audit.assignments[0].distance_km.toFixed(2)} km`
                    : "N/A"}
                </span>
              </p>
            </div>
          </div>
          <DriverMap
            driverLocation={{
              latitude: audit.driver_location.latitude,
              longitude: audit.driver_location.longitude,
              name: audit.driver_location.name,
              address: audit.driver_location.address,
            }}
            pickupLocation={
              audit.order_details?.pickup_address &&
              Number.isFinite(pickupLat) &&
              Number.isFinite(pickupLng)
                ? {
                    latitude: pickupLat,
                    longitude: pickupLng,
                    address: audit.order_details.pickup_address,
                  }
                : undefined
            }
            dropoffLocation={
              audit.order_details?.dropoff_address &&
              Number.isFinite(dropoffLat) &&
              Number.isFinite(dropoffLng)
                ? {
                    latitude: dropoffLat,
                    longitude: dropoffLng,
                    address: audit.order_details.dropoff_address,
                  }
                : undefined
            }
          />
        </motion.div>
      )}
    </div>
  );
}
