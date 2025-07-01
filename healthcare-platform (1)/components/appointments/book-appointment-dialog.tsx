"use client"

import type React from "react"

import { useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2 } from "lucide-react"

interface BookAppointmentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: () => void
}

export function BookAppointmentDialog({ open, onOpenChange, onSuccess }: BookAppointmentDialogProps) {
  const [formData, setFormData] = useState({
    doctor_id: "",
    title: "",
    description: "",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch("http://localhost:5000/appointments", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          doctor_id: Number.parseInt(formData.doctor_id),
          title: formData.title,
          description: formData.description,
        }),
      })

      if (response.ok) {
        onSuccess()
        onOpenChange(false)
        setFormData({ doctor_id: "", title: "", description: "" })
      } else {
        const data = await response.json()
        setError(data.error || "Failed to book appointment")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Book New Appointment</DialogTitle>
          <DialogDescription>Fill in the details to book an appointment with a doctor.</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="doctor_id">Doctor ID</Label>
            <Input
              id="doctor_id"
              type="number"
              value={formData.doctor_id}
              onChange={(e) => setFormData((prev) => ({ ...prev, doctor_id: e.target.value }))}
              placeholder="Enter doctor ID"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">Appointment Title</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="e.g., Regular Checkup"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Describe your symptoms or reason for visit"
              className="min-h-[100px]"
              required
            />
          </div>

          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Book Appointment
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
