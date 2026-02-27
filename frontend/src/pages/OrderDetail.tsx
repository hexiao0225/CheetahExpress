import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Package,
  User,
  Phone,
  CheckCircle2,
  XCircle,
  MapPin,
} from "lucide-react";
import { Link } from "react-router-dom";
import { orderApi } from "../utils/api";
import { motion } from "framer-motion";
import DriverMap from "../components/DriverMap";

export default function OrderDetail() {
  const { orderId } = useParams<{ orderId: string }>();

  const { data: audit, isLoading } = useQuery({
    queryKey: ["orderAudit", orderId],
    queryFn: () => orderApi.getAuditTrail(orderId!).then((res) => res.data),
    enabled: !!orderId,
    refetchInterval: 5000, // Refresh every 5 seconds for live GPS tracking
  });

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
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Driver:{" "}
              <span className="font-medium text-gray-900">
                {audit.driver_location.name}
              </span>
            </p>
            <p className="text-sm text-gray-600">
              Current Location:{" "}
              <span className="font-medium text-gray-900">
                {audit.driver_location.address}
              </span>
            </p>
          </div>
          <DriverMap
            driverLocation={{
              latitude: audit.driver_location.latitude,
              longitude: audit.driver_location.longitude,
              name: audit.driver_location.name,
              address: audit.driver_location.address,
            }}
            pickupLocation={
              audit.order_details?.pickup_address
                ? {
                    latitude: 37.7749,
                    longitude: -122.4194,
                    address: audit.order_details.pickup_address,
                  }
                : undefined
            }
            dropoffLocation={
              audit.order_details?.dropoff_address
                ? {
                    latitude: 37.7849,
                    longitude: -122.4094,
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
