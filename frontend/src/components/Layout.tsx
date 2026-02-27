import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Package, 
  Users, 
  Phone, 
  BarChart3,
  Zap
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Orders', href: '/orders', icon: Package },
  { name: 'Drivers', href: '/drivers', icon: Users },
  { name: 'Call Sessions', href: '/call-sessions', icon: Phone },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-gradient-to-b from-cheetah-600 to-cheetah-800 text-white">
        <div className="flex h-16 items-center gap-2 px-6 border-b border-cheetah-700">
          <Zap className="h-8 w-8" />
          <div>
            <h1 className="text-xl font-bold">Cheetah Express</h1>
            <p className="text-xs text-cheetah-200">AI-Powered Dispatch</p>
          </div>
        </div>
        
        <nav className="mt-6 px-3">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all
                  ${isActive 
                    ? 'bg-white text-cheetah-700 shadow-lg' 
                    : 'text-cheetah-100 hover:bg-cheetah-700'
                  }
                `}
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-cheetah-700">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-cheetah-500 flex items-center justify-center font-bold">
              AD
            </div>
            <div className="text-sm">
              <p className="font-medium">Admin User</p>
              <p className="text-cheetah-300 text-xs">admin@cheetah.com</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="ml-64">
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
