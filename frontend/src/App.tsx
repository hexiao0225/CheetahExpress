import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Orders from "./pages/Orders";
import Drivers from "./pages/Drivers";
import CallSessions from "./pages/CallSessions";
import Analytics from "./pages/Analytics";
import OrderDetail from "./pages/OrderDetail";
import OrdersGraph from "./pages/OrdersGraph";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="orders" element={<Orders />} />
        <Route path="orders/graph" element={<OrdersGraph />} />
        <Route path="orders/:orderId" element={<OrderDetail />} />
        <Route path="drivers" element={<Drivers />} />
        <Route path="call-sessions" element={<CallSessions />} />
        <Route path="analytics" element={<Analytics />} />
      </Route>
    </Routes>
  );
}

export default App;
