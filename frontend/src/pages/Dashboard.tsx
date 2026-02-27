import { useQuery } from "@tanstack/react-query";
import {
  Package,
  Users,
  Phone,
  TrendingUp,
  Clock,
  CheckCircle2,
} from "lucide-react";
import StatCard from "../components/StatCard";
import { orderApi } from "../utils/api";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: mockOrders } = useQuery({
    queryKey: ["mockOrders"],
    queryFn: () => orderApi.getMockOrders().then((res) => res.data),
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Real-time overview of your dispatch operations
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Orders Today"
          value="24"
          icon={Package}
          trend={{ value: 12, isPositive: true }}
          color="blue"
        />
        <StatCard
          title="Active Drivers"
          value="8"
          icon={Users}
          trend={{ value: 5, isPositive: true }}
          color="green"
          onClick={() => navigate("/drivers")}
        />
        <StatCard title="Calls Made" value="156" icon={Phone} color="orange" />
        <StatCard
          title="Success Rate"
          value="94%"
          icon={TrendingUp}
          trend={{ value: 3, isPositive: true }}
          color="purple"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Orders
            </h2>
            <span
              onClick={() => navigate("/orders")}
              className="text-sm text-cheetah-600 font-medium cursor-pointer hover:text-cheetah-700"
            >
              View All →
            </span>
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                onClick={() => navigate("/orders")}
                className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="h-10 w-10 rounded-full bg-cheetah-100 flex items-center justify-center">
                  <Package className="h-5 w-5 text-cheetah-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Order #ORD00{i}</p>
                  <p className="text-sm text-gray-500">
                    Market St → Mission St
                  </p>
                </div>
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                  Assigned
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Mock Orders Available */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gradient-to-br from-cheetah-500 to-cheetah-600 rounded-xl shadow-lg p-6 text-white"
        >
          <div className="flex items-center gap-3 mb-4">
            <Clock className="h-6 w-6" />
            <h2 className="text-lg font-semibold">Mock Orders Available</h2>
          </div>
          <p className="text-cheetah-100 mb-4">
            {mockOrders?.count || 0} test orders ready for dispatch
          </p>
          <div className="space-y-2">
            {mockOrders?.orders.slice(0, 3).map((order) => (
              <div
                key={order.order_id}
                className="bg-white/10 backdrop-blur-sm rounded-lg p-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{order.order_id}</span>
                  <span className="text-xs bg-white/20 px-2 py-1 rounded">
                    {order.vehicle_type}
                  </span>
                </div>
                <p className="text-sm text-cheetah-100 mt-1">
                  Priority: {order.priority}/10
                </p>
              </div>
            ))}
          </div>
          <button
            onClick={() => navigate("/orders")}
            className="mt-4 w-full bg-white text-cheetah-600 font-medium py-2 px-4 rounded-lg hover:bg-cheetah-50 transition-colors"
          >
            View All Mock Orders
          </button>
        </motion.div>
      </div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          System Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-sm font-medium text-gray-900">
                Neo4j Database
              </p>
              <p className="text-xs text-gray-500">Connected</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-sm font-medium text-gray-900">Mock Mode</p>
              <p className="text-xs text-gray-500">Active</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-500" />
            <div>
              <p className="text-sm font-medium text-gray-900">API Server</p>
              <p className="text-xs text-gray-500">Running</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
