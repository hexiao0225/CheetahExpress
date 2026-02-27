import { BarChart3, TrendingUp, Users, Package } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const orderTrendData = [
  { name: "Mon", orders: 12 },
  { name: "Tue", orders: 19 },
  { name: "Wed", orders: 15 },
  { name: "Thu", orders: 22 },
  { name: "Fri", orders: 28 },
  { name: "Sat", orders: 18 },
  { name: "Sun", orders: 14 },
];

const vehicleTypeData = [
  { name: "Sedan", value: 45 },
  { name: "SUV", value: 25 },
  { name: "Van", value: 20 },
  { name: "Truck", value: 10 },
];

const COLORS = ["#f97316", "#3b82f6", "#10b981", "#8b5cf6"];

export default function Analytics() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Analytics & Insights
        </h1>
        <p className="text-gray-600 mt-1">
          Performance metrics and business intelligence
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
          <Package className="h-8 w-8 mb-3 opacity-80" />
          <p className="text-sm opacity-90">Total Orders</p>
          <p className="text-3xl font-bold mt-1">128</p>
          <p className="text-xs mt-2 opacity-75">+12% from last week</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white">
          <TrendingUp className="h-8 w-8 mb-3 opacity-80" />
          <p className="text-sm opacity-90">Success Rate</p>
          <p className="text-3xl font-bold mt-1">94%</p>
          <p className="text-xs mt-2 opacity-75">+3% from last week</p>
        </div>
        <div className="bg-gradient-to-br from-cheetah-500 to-cheetah-600 rounded-xl p-6 text-white">
          <Users className="h-8 w-8 mb-3 opacity-80" />
          <p className="text-sm opacity-90">Active Drivers</p>
          <p className="text-3xl font-bold mt-1">8</p>
          <p className="text-xs mt-2 opacity-75">All shifts covered</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white">
          <BarChart3 className="h-8 w-8 mb-3 opacity-80" />
          <p className="text-sm opacity-90">Avg Response</p>
          <p className="text-3xl font-bold mt-1">45s</p>
          <p className="text-xs mt-2 opacity-75">-8s from last week</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order Trend */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Order Trend (Last 7 Days)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={orderTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="orders"
                stroke="#f97316"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Vehicle Type Distribution */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Orders by Vehicle Type
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={vehicleTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {vehicleTypeData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Driver Performance
        </h3>
        <div className="space-y-4">
          {["John Smith", "Sarah Johnson", "Mike Chen"].map((driver, index) => (
            <div key={driver} className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-900">
                    {driver}
                  </span>
                  <span className="text-sm text-gray-600">
                    {95 - index * 3}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cheetah-500 to-cheetah-600"
                    style={{ width: `${95 - index * 3}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
