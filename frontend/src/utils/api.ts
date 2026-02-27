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

export interface OrdersGraphEdge {
  order_id: string
  status?: string
  driver_id?: string | null
  driver_name?: string | null
  distance_km?: number | null
  duration_hours?: number | null
  assigned_at?: string | null
}

export interface OrdersGraphResponse {
  count: number
  orders: OrdersGraphEdge[]
  drivers: {
    driver_id: string
    driver_name: string
  }[]
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

export interface VoiceCallEntry {
  driver_id: string
  outcome: string
  sentiment?: number
  decline_reason?: string
  transcript?: string
}

export interface AuditTrail {
  order_id: string
  order_details: any
  compliance_checks: any[]
  rankings: any[]
  voice_calls: VoiceCallEntry[]
  assignments: any[]
  driver_location?: {
    driver_id: string
    name: string
    phone: string
    vehicle_type?: string
    license_number?: string
    license_expiry?: string
    is_available?: boolean
    latitude: number
    longitude: number
    address: string
  }
}

export interface DemoCallResult {
  order_id: string
  driver_id: string
  driver_name: string
  phone: string
  outcome: 'accepted' | 'declined' | 'no_answer' | 'failed'
  sentiment_score?: number
  decline_reason?: string
  transcript?: string
  call_duration_seconds?: number
}

export interface DemoCallScript {
  script: string
  driver_name: string
  driver_id: string
  order_id: string
}

export interface DemoTranscribeResult {
  order_id: string
  driver_id: string
  driver_name: string
  transcript: string
  outcome: string
  decline_reason?: string
  sentiment_score: number
  response_message: string
}

export const orderApi = {
  getMockOrders: () => api.get<{ count: number; orders: MockOrder[] }>('/mock/orders'),
  submitMockOrder: (orderId: string) => api.post<Order>(`/mock/orders/${orderId}`),
  getOrderStatus: (orderId: string) => api.get<Order>(`/orders/${orderId}`),
  getAuditTrail: (orderId: string) => api.get<AuditTrail>(`/orders/${orderId}/audit`),
  getOrdersGraph: () => api.get<OrdersGraphResponse>('/orders_graph'),
  createOrder: (order: any) => api.post<Order>('/orders', order),
  triggerDemoCall: () => api.post<DemoCallResult>('/demo/call'),
  getDemoCallScript: () => api.get<DemoCallScript>('/demo/call/script'),
  transcribeDemoCall: (audioBlob: Blob) => {
    const form = new FormData()
    const isWav = audioBlob.type === 'audio/wav' || audioBlob.type === 'audio/wave'
    form.append('audio', audioBlob, isWav ? 'recording.wav' : 'recording.webm')
    return api.post<DemoTranscribeResult>('/demo/call/transcribe', form, {
      timeout: 60000,
    })
  },
}

export default api
