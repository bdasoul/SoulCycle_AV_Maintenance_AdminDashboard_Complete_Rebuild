import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx'
import { 
  Building2, 
  Settings, 
  AlertTriangle, 
  Calendar, 
  BarChart3, 
  FileText,
  Wrench,
  Mic,
  Volume2,
  Cpu,
  Zap,
  CheckCircle,
  Clock,
  AlertCircle,
  TrendingUp
} from 'lucide-react'
import './App.css'

// API base URL
const API_BASE = '/api'

// Main Dashboard Component
function Dashboard() {
  const [stats, setStats] = useState({
    studios: { total: 0, active: 0 },
    equipment: { total: 0, critical: 0, maintenance_due: 0 },
    alerts: { unread: 0, critical: 0 },
    maintenance: { overdue: 0, upcoming: 0 }
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      setLoading(true)
      // Fetch stats from multiple endpoints
      const [studiosRes, equipmentRes, alertsRes] = await Promise.all([
        fetch(`${API_BASE}/studios`),
        fetch(`${API_BASE}/equipment/stats`),
        fetch(`${API_BASE}/alerts/stats`)
      ])

      const studiosData = await studiosRes.json()
      const equipmentData = await equipmentRes.json()
      const alertsData = await alertsRes.json()

      setStats({
        studios: {
          total: studiosData.count || 0,
          active: studiosData.data?.filter(s => s.is_active).length || 0
        },
        equipment: {
          total: equipmentData.data?.total_equipment || 0,
          critical: equipmentData.data?.critical_equipment || 0,
          maintenance_due: equipmentData.data?.maintenance?.due_soon || 0
        },
        alerts: {
          unread: alertsData.data?.unread_alerts || 0,
          critical: alertsData.data?.by_priority?.critical || 0
        },
        maintenance: {
          overdue: equipmentData.data?.maintenance?.overdue || 0,
          upcoming: equipmentData.data?.maintenance?.due_soon || 0
        }
      })
    } catch (error) {
      console.error('Error fetching dashboard stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const StatCard = ({ title, value, subtitle, icon: Icon, variant = "default" }) => (
    <Card className={`transition-all duration-200 hover:shadow-lg ${
      variant === "warning" ? "border-orange-200 bg-orange-50" :
      variant === "danger" ? "border-red-200 bg-red-50" :
      variant === "success" ? "border-green-200 bg-green-50" :
      "hover:border-blue-200"
    }`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-2xl font-bold ${
              variant === "warning" ? "text-orange-700" :
              variant === "danger" ? "text-red-700" :
              variant === "success" ? "text-green-700" :
              "text-gray-900"
            }`}>
              {loading ? "..." : value}
            </p>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <Icon className={`h-8 w-8 ${
            variant === "warning" ? "text-orange-600" :
            variant === "danger" ? "text-red-600" :
            variant === "success" ? "text-green-600" :
            "text-blue-600"
          }`} />
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AV Maintenance Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and manage audio-visual equipment across all SoulCycle studios</p>
        </div>
        <Button onClick={fetchDashboardStats} disabled={loading}>
          <TrendingUp className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
      </div>

      {/* Critical Alerts */}
      {stats.alerts.critical > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Critical Alerts</AlertTitle>
          <AlertDescription className="text-red-700">
            You have {stats.alerts.critical} critical alerts requiring immediate attention.
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Studios"
          value={stats.studios.total}
          subtitle={`${stats.studios.active} active`}
          icon={Building2}
          variant="default"
        />
        <StatCard
          title="Equipment Items"
          value={stats.equipment.total}
          subtitle={`${stats.equipment.critical} critical`}
          icon={Settings}
          variant="default"
        />
        <StatCard
          title="Overdue Maintenance"
          value={stats.maintenance.overdue}
          subtitle="Requires immediate attention"
          icon={AlertCircle}
          variant={stats.maintenance.overdue > 0 ? "danger" : "success"}
        />
        <StatCard
          title="Upcoming Maintenance"
          value={stats.maintenance.upcoming}
          subtitle="Due within 30 days"
          icon={Clock}
          variant={stats.maintenance.upcoming > 5 ? "warning" : "default"}
        />
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common maintenance management tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <Calendar className="h-6 w-6" />
              <span>Schedule Maintenance</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <AlertTriangle className="h-6 w-6" />
              <span>View Alerts</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col space-y-2">
              <FileText className="h-6 w-6" />
              <span>Generate Report</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Equipment Categories Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Equipment Categories</CardTitle>
          <CardDescription>Overview of AV equipment types across all studios</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3 p-4 rounded-lg bg-blue-50 border border-blue-200">
              <Volume2 className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-semibold text-blue-900">Amplifiers</p>
                <p className="text-sm text-blue-700">High-power audio</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-4 rounded-lg bg-green-50 border border-green-200">
              <Mic className="h-8 w-8 text-green-600" />
              <div>
                <p className="font-semibold text-green-900">Microphones</p>
                <p className="text-sm text-green-700">Wireless systems</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-4 rounded-lg bg-purple-50 border border-purple-200">
              <Cpu className="h-8 w-8 text-purple-600" />
              <div>
                <p className="font-semibold text-purple-900">DSP Units</p>
                <p className="text-sm text-purple-700">Signal processing</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-4 rounded-lg bg-orange-50 border border-orange-200">
              <Zap className="h-8 w-8 text-orange-600" />
              <div>
                <p className="font-semibold text-orange-900">Power Systems</p>
                <p className="text-sm text-orange-700">Distribution & UPS</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Studios Management Component
function Studios() {
  const [studios, setStudios] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStudios()
  }, [])

  const fetchStudios = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/studios`)
      const data = await response.json()
      setStudios(data.data || [])
    } catch (error) {
      console.error('Error fetching studios:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Studios</h1>
          <p className="text-gray-600 mt-1">Manage SoulCycle studio locations and their AV equipment</p>
        </div>
        <Button>
          <Building2 className="h-4 w-4 mr-2" />
          Add Studio
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading studios...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {studios.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="text-center py-12">
                <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Studios Found</h3>
                <p className="text-gray-600 mb-4">Get started by adding your first SoulCycle studio location.</p>
                <Button>Add Your First Studio</Button>
              </CardContent>
            </Card>
          ) : (
            studios.map((studio) => (
              <Card key={studio.id} className="hover:shadow-lg transition-shadow duration-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{studio.name}</CardTitle>
                    <Badge variant={studio.is_active ? "default" : "secondary"}>
                      {studio.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <CardDescription>{studio.location}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Capacity:</span>
                      <span className="font-medium">{studio.capacity || "N/A"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Classes/Day:</span>
                      <span className="font-medium">{studio.classes_per_day || "N/A"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Manager:</span>
                      <span className="font-medium">{studio.manager_name || "N/A"}</span>
                    </div>
                  </div>
                  <div className="flex space-x-2 mt-4">
                    <Button variant="outline" size="sm" className="flex-1">
                      <Settings className="h-4 w-4 mr-1" />
                      Equipment
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1">
                      <Wrench className="h-4 w-4 mr-1" />
                      Maintenance
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  )
}

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState("dashboard")

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
                  <Wrench className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">SoulCycle</h1>
                  <p className="text-xs text-gray-600">AV Maintenance</p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                System Online
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="dashboard" className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="studios" className="flex items-center space-x-2">
              <Building2 className="h-4 w-4" />
              <span>Studios</span>
            </TabsTrigger>
            <TabsTrigger value="equipment" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span>Equipment</span>
            </TabsTrigger>
            <TabsTrigger value="maintenance" className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>Maintenance</span>
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center space-x-2">
              <FileText className="h-4 w-4" />
              <span>Reports</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <Dashboard />
          </TabsContent>

          <TabsContent value="studios">
            <Studios />
          </TabsContent>

          <TabsContent value="equipment">
            <div className="text-center py-12">
              <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Equipment Management</h3>
              <p className="text-gray-600">Equipment management interface coming soon...</p>
            </div>
          </TabsContent>

          <TabsContent value="maintenance">
            <div className="text-center py-12">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Maintenance Scheduling</h3>
              <p className="text-gray-600">Maintenance scheduling interface coming soon...</p>
            </div>
          </TabsContent>

          <TabsContent value="reports">
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Reports & Analytics</h3>
              <p className="text-gray-600">Reporting interface coming soon...</p>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App

