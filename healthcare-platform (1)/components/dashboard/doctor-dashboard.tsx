"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calendar, Clock, Users, LogOut } from "lucide-react"
import { AppointmentsList } from "@/components/appointments/appointments-list"
import { ChatInterface } from "@/components/chat/chat-interface"
import { ProfileCard } from "@/components/profile/profile-card"

interface DoctorData {
  id: number
  name: string
  email: string
  specialization: string
  phone_number: string
  experience: number
}

interface Appointment {
  id: number
  title: string
  description: string
  date_created: string
  date_appointment: string
  patient_id: number
  doctor_id: number
  status: string
}

export function DoctorDashboard() {
  const [doctorData, setDoctorData] = useState<DoctorData | null>(null)
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDoctorData()
    fetchAppointments()
  }, [])

  const fetchDoctorData = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch("http://localhost:5000/get_doctors_data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ id: 1 }),
      })

      if (response.ok) {
        const data = await response.json()
        setDoctorData(data)
      }
    } catch (error) {
      console.error("Failed to fetch doctor data:", error)
    }
  }

  const fetchAppointments = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch("http://localhost:5000/get_doctors_appointment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ id: 1 }),
      })

      if (response.ok) {
        const data = await response.json()
        setAppointments(data.appointments || [])
      }
    } catch (error) {
      console.error("Failed to fetch appointments:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("user_role")
    window.location.href = "/"
  }

  const pendingAppointments = appointments.filter((apt) => apt.status === "Pending")
  const todayAppointments = appointments.filter((apt) => {
    const today = new Date().toDateString()
    const aptDate = new Date(apt.date_appointment).toDateString()
    return today === aptDate
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Doctor Dashboard</h1>
              <p className="text-gray-600">Welcome back, Dr. {doctorData?.name}</p>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Appointments</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{appointments.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Requests</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{pendingAppointments.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Today&apos;s Appointments</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{todayAppointments.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Experience</CardTitle>
              <Badge variant="secondary">{doctorData?.experience} years</Badge>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">{doctorData?.specialization}</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="appointments" className="space-y-6">
          <TabsList>
            <TabsTrigger value="appointments">Appointments</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
          </TabsList>

          <TabsContent value="appointments">
            <AppointmentsList appointments={appointments} userRole="doctor" onAppointmentUpdate={fetchAppointments} />
          </TabsContent>

          <TabsContent value="messages">
            <ChatInterface userType="doctor" userId={doctorData?.id || 1} />
          </TabsContent>

          <TabsContent value="profile">
            <ProfileCard userData={doctorData} userType="doctor" />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
