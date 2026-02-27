import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

export interface Order {
  order_id: string
  status: string
  assigned_driver_id?: string
  assigned_driver_name?: string
  total_drivers_considered: number
  total_drivers_called: number
  processing_time_seconds: number
  message: string
  pickup?: {
    address: string
    latitude: number
    longitude: number
  }
  dropoff?: {
    address: string
    latitude: number
    longitude: number
  }
  vehicle_type?: string
  customer_info?: {
    name: string
    phone: string
    email?: string
  }
}

export interface MockOrder {
  order_id: string
  pickup: {
    address: string
    latitude: number
    longitude: number
  }
  dropoff: {
    address: string
    latitude: number
    longitude: number
  }
  time_window: {
    start: string
    end: string
  }
  vehicle_type: string
  customer_info: {
    name: string
    phone: string
    email?: string
  }
  special_instructions?: string
  priority: number
}

export interface AuditTrail {
  order_id: string
  order_details: any
  compliance_checks: any[]
  rankings: any[]
  voice_calls: any[]
  assignments: any[]
  driver_location?: {
    driver_id: string
    name: string
    phone: string
    latitude: number
    longitude: number
    address: string
  }
}

export const orderApi = {
  getMockOrders: () => api.get<{ count: number; orders: MockOrder[] }>('/mock/orders'),
  submitMockOrder: (orderId: string) => api.post<Order>(`/mock/orders/${orderId}`),
  getOrderStatus: (orderId: string) => api.get<Order>(`/orders/${orderId}`),
  getAuditTrail: (orderId: string) => api.get<AuditTrail>(`/orders/${orderId}/audit`),
  createOrder: (order: any) => api.post<Order>('/orders', order),
}

export default api
