"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Calendar, Clock, User, CheckCircle, XCircle } from "lucide-react"
import { format } from "date-fns"

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

interface AppointmentsListProps {
  appointments: Appointment[]
  userRole: "doctor" | "patient"
  onAppointmentUpdate: () => void
}

export function AppointmentsList({ appointments, userRole, onAppointmentUpdate }: AppointmentsListProps) {
  const [loading, setLoading] = useState<number | null>(null)

  const handleStatusUpdate = async (appointmentId: number, action: string) => {
    setLoading(appointmentId)
    try {
      const token = localStorage.getItem("access_token")
      let endpoint = ""

      switch (action) {
        case "confirm":
          endpoint = `http://localhost:5000/appointments/confirm_appointment/${appointmentId}`
          break
        case "complete":
          endpoint = `http://localhost:5000/appointments/appointment_completed/${appointmentId}`
          break
        case "cancel":
          endpoint = `http://localhost:5000/appointments/cancel_appointment/${appointmentId}`
          break
      }

      const response = await fetch(endpoint, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.ok) {
        onAppointmentUpdate()
      }
    } catch (error) {
      console.error("Failed to update appointment:", error)
    } finally {
      setLoading(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return "bg-yellow-100 text-yellow-800"
      case "confirmed":
        return "bg-blue-100 text-blue-800"
      case "completed":
        return "bg-green-100 text-green-800"
      case "cancelled":
        return "bg-red-100 text-red-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  if (appointments.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Calendar className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No appointments yet</h3>
          <p className="text-gray-600 text-center">
            {userRole === "patient"
              ? "Book your first appointment to get started"
              : "No appointments scheduled at the moment"}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {appointments.map((appointment) => (
        <Card key={appointment.id}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-lg">{appointment.title}</CardTitle>
                <CardDescription className="mt-1">{appointment.description}</CardDescription>
              </div>
              <Badge className={getStatusColor(appointment.status)}>{appointment.status}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {appointment.date_appointment
                    ? format(new Date(appointment.date_appointment), "MMM dd, yyyy")
                    : "Date TBD"}
                </div>
                <div className="flex items-center">
                  <Clock className="h-4 w-4 mr-1" />
                  {appointment.date_appointment
                    ? format(new Date(appointment.date_appointment), "hh:mm a")
                    : "Time TBD"}
                </div>
                <div className="flex items-center">
                  <User className="h-4 w-4 mr-1" />
                  {userRole === "doctor"
                    ? `Patient ID: ${appointment.patient_id}`
                    : `Doctor ID: ${appointment.doctor_id}`}
                </div>
              </div>

              <div className="flex space-x-2">
                {userRole === "doctor" && appointment.status === "Pending" && (
                  <Button
                    size="sm"
                    onClick={() => handleStatusUpdate(appointment.id, "confirm")}
                    disabled={loading === appointment.id}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Confirm
                  </Button>
                )}

                {appointment.status === "Confirmed" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusUpdate(appointment.id, "complete")}
                    disabled={loading === appointment.id}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Complete
                  </Button>
                )}

                {appointment.status !== "Completed" && appointment.status !== "Cancelled" && (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleStatusUpdate(appointment.id, "cancel")}
                    disabled={loading === appointment.id}
                  >
                    <XCircle className="h-4 w-4 mr-1" />
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
