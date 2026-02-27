import { User, MapPin, Car, Calendar, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

const mockDrivers = [
  {
    id: 'DRV001',
    name: 'John Smith',
    phone: '+1-555-0101',
    vehicle: 'Sedan',
    location: '450 Sutter St, San Francisco',
    status: 'available',
    ordersToday: 3,
    kmToday: 45.2,
    licenseExpiry: '2025-12-31',
  },
  {
    id: 'DRV002',
    name: 'Sarah Johnson',
    phone: '+1-555-0102',
    vehicle: 'SUV',
    location: '1 Market St, San Francisco',
    status: 'on_delivery',
    ordersToday: 5,
    kmToday: 67.8,
    licenseExpiry: '2026-06-30',
  },
  {
    id: 'DRV003',
    name: 'Mike Chen',
    phone: '+1-555-0103',
    vehicle: 'Van',
    location: '555 California St, San Francisco',
    status: 'available',
    ordersToday: 2,
    kmToday: 28.5,
    licenseExpiry: '2025-03-15',
  },
]

export default function Drivers() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 text-green-700'
      case 'on_delivery':
        return 'bg-blue-100 text-blue-700'
      case 'offline':
        return 'bg-gray-100 text-gray-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Driver Management</h1>
        <p className="text-gray-600 mt-1">Monitor and manage your driver fleet</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Drivers</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{mockDrivers.length}</p>
            </div>
            <User className="h-8 w-8 text-cheetah-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Available</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {mockDrivers.filter(d => d.status === 'available').length}
              </p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">On Delivery</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {mockDrivers.filter(d => d.status === 'on_delivery').length}
              </p>
            </div>
            <Car className="h-8 w-8 text-blue-600" />
          </div>
        </div>
      </div>

      {/* Drivers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {mockDrivers.map((driver, index) => (
          <motion.div
            key={driver.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-14 w-14 rounded-full bg-gradient-to-br from-cheetah-500 to-cheetah-600 flex items-center justify-center text-white font-bold text-lg">
                  {driver.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{driver.name}</h3>
                  <p className="text-sm text-gray-500">{driver.id}</p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(driver.status)}`}>
                {driver.status.replace('_', ' ')}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="flex items-start gap-2">
                <Car className="h-4 w-4 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Vehicle</p>
                  <p className="text-sm font-medium text-gray-900">{driver.vehicle}</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-500">Location</p>
                  <p className="text-sm font-medium text-gray-900">{driver.location.split(',')[0]}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg mb-4">
              <div>
                <p className="text-xs text-gray-500">Orders Today</p>
                <p className="text-lg font-bold text-gray-900">{driver.ordersToday}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">KM Today</p>
                <p className="text-lg font-bold text-gray-900">{driver.kmToday}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Remaining</p>
                <p className="text-lg font-bold text-green-600">{(300 - driver.kmToday).toFixed(0)}</p>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar className="h-4 w-4" />
                <span>License: {driver.licenseExpiry}</span>
              </div>
              <button className="text-cheetah-600 hover:text-cheetah-700 font-medium">
                View Details →
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
