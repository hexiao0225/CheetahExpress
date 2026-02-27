import { useState } from "react";
import {
  Phone,
  User,
  Clock,
  TrendingUp,
  CheckCircle2,
  XCircle,
  PhoneOff,
} from "lucide-react";
import { motion } from "framer-motion";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { orderApi } from "../utils/api";
import { toast } from "sonner";

interface CallSession {
  id: string;
  orderId: string;
  driverId: string;
  driverName: string;
  outcome: "accepted" | "declined" | "no_answer";
  sentiment: number;
  duration: number;
  timestamp: string;
  declineReason?: string;
}

const mockCallSessions: CallSession[] = [
  {
    id: "CALL001",
    orderId: "ORD001",
    driverId: "DRV001",
    driverName: "John Smith",
    outcome: "accepted",
    sentiment: 0.85,
    duration: 32,
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: "CALL002",
    orderId: "ORD001",
    driverId: "DRV003",
    driverName: "Mike Chen",
    outcome: "declined",
    sentiment: 0.45,
    duration: 28,
    timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    declineReason: "Already have another delivery",
  },
  {
    id: "CALL003",
    orderId: "ORD002",
    driverId: "DRV002",
    driverName: "Sarah Johnson",
    outcome: "accepted",
    sentiment: 0.92,
    duration: 25,
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
];

export default function CallSessions() {
  const [filter, setFilter] = useState<"all" | "accepted" | "declined">("all");
  const navigate = useNavigate();

  const demoCallMutation = useMutation({
    mutationFn: (orderId: string) => orderApi.submitMockOrder(orderId),
    onSuccess: (res) => {
      toast.success(`Demo started for ${res.data.order_id}`);
      navigate(`/orders/${res.data.order_id}`);
    },
    onError: (error: any) => {
      toast.error(`Demo failed: ${error?.message || "Unknown error"}`);
    },
  });

  const filteredSessions = mockCallSessions.filter((session) => {
    if (filter === "all") return true;
    return session.outcome === filter;
  });

  const getOutcomeIcon = (outcome: string) => {
    switch (outcome) {
      case "accepted":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "declined":
        return <XCircle className="h-5 w-5 text-red-600" />;
      case "no_answer":
        return <PhoneOff className="h-5 w-5 text-gray-600" />;
      default:
        return <Phone className="h-5 w-5 text-gray-600" />;
    }
  };

  const getOutcomeColor = (outcome: string) => {
    switch (outcome) {
      case "accepted":
        return "bg-green-100 text-green-700";
      case "declined":
        return "bg-red-100 text-red-700";
      case "no_answer":
        return "bg-gray-100 text-gray-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return "text-green-600";
    if (sentiment >= 0.5) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Call Sessions</h1>
        <p className="text-gray-600 mt-1">
          Real-time voice dispatch monitoring with AI sentiment analysis
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            Live Demo Trigger
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Click to run a full dispatch flow and jump to the order detail page
            to watch call outcomes.
          </p>
        </div>
        <button
          onClick={() => demoCallMutation.mutate("ORD002")}
          disabled={demoCallMutation.isPending}
          className="bg-cheetah-600 text-white px-4 py-2 rounded-lg hover:bg-cheetah-700 transition-colors disabled:opacity-60"
        >
          {demoCallMutation.isPending
            ? "Running demo..."
            : "Run Call Demo (ORD002)"}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Calls</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {mockCallSessions.length}
              </p>
            </div>
            <Phone className="h-8 w-8 text-cheetah-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Accepted</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {
                  mockCallSessions.filter((s) => s.outcome === "accepted")
                    .length
                }
              </p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Declined</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {
                  mockCallSessions.filter((s) => s.outcome === "declined")
                    .length
                }
              </p>
            </div>
            <XCircle className="h-8 w-8 text-red-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Sentiment</p>
              <p className="text-2xl font-bold text-cheetah-600 mt-1">
                {(
                  (mockCallSessions.reduce((acc, s) => acc + s.sentiment, 0) /
                    mockCallSessions.length) *
                  100
                ).toFixed(0)}
                %
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-cheetah-600" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(["all", "accepted", "declined"] as const).map((filterOption) => (
          <button
            key={filterOption}
            onClick={() => setFilter(filterOption)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === filterOption
                ? "bg-cheetah-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
            }`}
          >
            {filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
          </button>
        ))}
      </div>

      {/* Call Sessions List */}
      <div className="space-y-4">
        {filteredSessions.map((session, index) => (
          <motion.div
            key={session.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-1">
                <div className="h-12 w-12 rounded-full bg-cheetah-100 flex items-center justify-center">
                  <User className="h-6 w-6 text-cheetah-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900">
                      {session.driverName}
                    </h3>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getOutcomeColor(session.outcome)}`}
                    >
                      {session.outcome}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Order ID</p>
                      <p className="font-medium text-gray-900">
                        {session.orderId}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Driver ID</p>
                      <p className="font-medium text-gray-900">
                        {session.driverId}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Duration</p>
                      <p className="font-medium text-gray-900">
                        {session.duration}s
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Sentiment Score</p>
                      <p
                        className={`font-bold ${getSentimentColor(session.sentiment)}`}
                      >
                        {(session.sentiment * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                  {session.declineReason && (
                    <div className="mt-3 p-3 bg-red-50 rounded-lg">
                      <p className="text-xs text-red-600 font-medium mb-1">
                        Decline Reason
                      </p>
                      <p className="text-sm text-red-900">
                        {session.declineReason}
                      </p>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                {getOutcomeIcon(session.outcome)}
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock className="h-3 w-3" />
                  {new Date(session.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Sentiment Visualization */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>Sentiment Analysis</span>
                <span>{(session.sentiment * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    session.sentiment >= 0.7
                      ? "bg-green-500"
                      : session.sentiment >= 0.5
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${session.sentiment * 100}%` }}
                />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
