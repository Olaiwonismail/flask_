"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calendar, Clock, MessageSquare, Plus, LogOut } from "lucide-react"
import { AppointmentsList } from "@/components/appointments/appointments-list"
import { ChatInterface } from "@/components/chat/chat-interface"
import { ProfileCard } from "@/components/profile/profile-card"
import { BookAppointmentDialog } from "@/components/appointments/book-appointment-dialog"

interface PatientData {
  id: number
  name: string
  email: string
  phone: string
  age: number
  gender: string
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

export function PatientDashboard() {
  const [patientData, setPatientData] = useState<PatientData | null>(null)
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [showBookDialog, setShowBookDialog] = useState(false)

  useEffect(() => {
    fetchPatientData()
    fetchAppointments()
  }, [])

  const fetchPatientData = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const id = localStorage.getItem("user_id") // Default to 1 if no ID found
      
      const response = await fetch("http://localhost:5000/get_patients_data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ id: id }), // Replace with actual patient ID
      })

      if (response.ok) {
        const data = await response.json()
        setPatientData(data)
      }
    } catch (error) {
      console.error("Failed to fetch patient data:", error)
    }
  }

  const fetchAppointments = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const id = localStorage.getItem("user_id")
      const response = await fetch("http://localhost:5000/get_patients_appointment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ id: id }), // Replace with actual patient ID
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

  const upcomingAppointments = appointments.filter(
    (apt) => new Date(apt.date_appointment) > new Date() && apt.status !== "Cancelled",
  )

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
              <h1 className="text-2xl font-bold text-gray-900">Patient Dashboard</h1>
              <p className="text-gray-600">Welcome back, {patientData?.name}</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setShowBookDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Book Appointment
              </Button>
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
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
              <CardTitle className="text-sm font-medium">Upcoming</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{upcomingAppointments.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Messages</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">Unread messages</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="appointments" className="space-y-6">
          <TabsList>
            <TabsTrigger value="appointments">My Appointments</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
          </TabsList>

          <TabsContent value="appointments">
            <AppointmentsList appointments={appointments} userRole="patient" onAppointmentUpdate={fetchAppointments} />
          </TabsContent>

          <TabsContent value="messages">
            <ChatInterface userType="patient" userId={patientData?.id || 1} />
          </TabsContent>

          <TabsContent value="profile">
            <ProfileCard userData={patientData} userType="patient" />
          </TabsContent>
        </Tabs>
      </main>

      <BookAppointmentDialog open={showBookDialog} onOpenChange={setShowBookDialog} onSuccess={fetchAppointments} />
    </div>
  )
}
