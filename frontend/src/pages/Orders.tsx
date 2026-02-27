import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Package, Play, Clock, Share2 } from "lucide-react";
import { orderApi } from "../utils/api";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

export default function Orders() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedOrder, setSelectedOrder] = useState<string | null>(null);

  const { data: mockOrders, isLoading } = useQuery({
    queryKey: ["mockOrders"],
    queryFn: () => orderApi.getMockOrders().then((res) => res.data),
  });

  const submitOrderMutation = useMutation({
    mutationFn: (orderId: string) => orderApi.submitMockOrder(orderId),
    onSuccess: (data) => {
      toast.success(`Order ${data.data.order_id} processed successfully!`);
      queryClient.invalidateQueries({ queryKey: ["mockOrders"] });
      navigate(`/orders/${data.data.order_id}`);
    },
    onError: (error: any) => {
      toast.error(`Failed to process order: ${error.message}`);
    },
  });

  const handleSubmitOrder = (orderId: string) => {
    setSelectedOrder(orderId);
    submitOrderMutation.mutate(orderId);
  };

  const getStatusColor = (priority: number) => {
    if (priority >= 8) return "bg-red-100 text-red-700";
    if (priority >= 6) return "bg-orange-100 text-orange-700";
    return "bg-blue-100 text-blue-700";
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
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Order Management</h1>
          <p className="text-gray-600 mt-1">Submit and track delivery orders</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/orders/graph")}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-cheetah-300 text-cheetah-700 bg-cheetah-50 hover:bg-cheetah-100 transition-colors"
          >
            <Share2 className="h-4 w-4" />
            See all orders
          </button>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Package className="h-5 w-5" />
            <span>{mockOrders?.count || 0} mock orders available</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {mockOrders?.orders.map((order, index) => (
          <motion.div
            key={order.order_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-lg bg-cheetah-100 flex items-center justify-center">
                  <Package className="h-6 w-6 text-cheetah-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {order.order_id}
                  </h3>
                  <p className="text-sm text-gray-500">{order.vehicle_type}</p>
                </div>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.priority)}`}
              >
                Priority {order.priority}/10
              </span>
            </div>

            <div className="space-y-3 mb-4">
              <div className="flex items-start gap-2">
                <div className="h-5 w-5 rounded-full bg-green-100 flex items-center justify-center mt-0.5">
                  <div className="h-2 w-2 rounded-full bg-green-600"></div>
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Pickup</p>
                  <p className="text-sm font-medium text-gray-900">
                    {order.pickup.address}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <div className="h-5 w-5 rounded-full bg-red-100 flex items-center justify-center mt-0.5">
                  <div className="h-2 w-2 rounded-full bg-red-600"></div>
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-500">Dropoff</p>
                  <p className="text-sm font-medium text-gray-900">
                    {order.dropoff.address}
                  </p>
                </div>
              </div>
            </div>

            {order.special_instructions && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600 font-medium mb-1">
                  Special Instructions
                </p>
                <p className="text-sm text-blue-900">
                  {order.special_instructions}
                </p>
              </div>
            )}

            <div className="flex items-center gap-2 text-xs text-gray-500 mb-4">
              <Clock className="h-4 w-4" />
              <span>
                Window: {new Date(order.time_window.start).toLocaleTimeString()}{" "}
                - {new Date(order.time_window.end).toLocaleTimeString()}
              </span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleSubmitOrder(order.order_id)}
                disabled={
                  submitOrderMutation.isPending &&
                  selectedOrder === order.order_id
                }
                className="flex-1 flex items-center justify-center gap-2 bg-cheetah-600 text-white px-4 py-2 rounded-lg hover:bg-cheetah-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitOrderMutation.isPending &&
                selectedOrder === order.order_id ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Submit Order
                  </>
                )}
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
