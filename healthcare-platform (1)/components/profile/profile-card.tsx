"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { User, Award } from "lucide-react"

interface ProfileCardProps {
  userData: any
  userType: "doctor" | "patient"
}

export function ProfileCard({ userData, userType }: ProfileCardProps) {
  if (!userData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading profile...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="h-5 w-5 mr-2" />
            Personal Information
          </CardTitle>
          <CardDescription>Your basic profile details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Full Name</span>
            <span className="text-sm">{userData.name}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Email</span>
            <span className="text-sm">{userData.email}</span>
          </div>

          {userType === "patient" && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Age</span>
                <span className="text-sm">{userData.age} years</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Gender</span>
                <Badge variant="secondary">{userData.gender}</Badge>
              </div>

              {userData.phone && (
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">Phone</span>
                  <span className="text-sm">{userData.phone}</span>
                </div>
              )}
            </>
          )}

          {userType === "doctor" && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Phone</span>
                <span className="text-sm">{userData.phone_number}</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {userType === "doctor" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Award className="h-5 w-5 mr-2" />
              Professional Information
            </CardTitle>
            <CardDescription>Your medical credentials and expertise</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-500">Specialization</span>
              <Badge variant="outline">{userData.specialization}</Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-500">Experience</span>
              <span className="text-sm">{userData.experience} years</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
