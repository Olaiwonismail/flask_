"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Send, Video, Phone } from "lucide-react"
import { format } from "date-fns"
import io, { Socket } from "socket.io-client"

interface Message {
  id: number
  sender_type: string
  sender_id: number
  content: string
  timestamp: string
  read: boolean
}

interface Contact {
  id: number
  name: string
  type: "doctor" | "patient"
  specialization?: string
  experience?: number
  age?: number
  gender?: string
}

interface ChatInterfaceProps {
  userType: "doctor" | "patient"
  userId: number
}

interface IncomingCall {
  call_id: string
  caller: {
    type: string
    id: number
  }
}

export function ChatInterface({ userType, userId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState("")
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(false)
  const [contactsLoading, setContactsLoading] = useState(true)
  const [incomingCall, setIncomingCall] = useState<IncomingCall | null>(null)
  const [activeCall, setActiveCall] = useState<{ callId: string; status: string } | null>(null)
  const [localStream, setLocalStream] = useState<MediaStream | null>(null)
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null)
  const [peerConnection, setPeerConnection] = useState<RTCPeerConnection | null>(null)
  const socketRef = useRef<Socket | null>(null)
  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Initialize socket connection
  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) return

    socketRef.current = io("http://localhost:5000", {
      auth: { token },
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    })

    socketRef.current.on("connect", () => {
      console.log("Socket connected")
    })

    socketRef.current.on("incoming_call", (data: IncomingCall) => {
      console.log("Incoming call:", data)
      setIncomingCall(data)
    })

    socketRef.current.on("call_accepted", (data: { call_id: string }) => {
      console.log("Call accepted:", data.call_id)
      if (activeCall?.callId === data.call_id) {
        setActiveCall(prev => ({ ...prev!, status: "ongoing" }))
      }
    })

    socketRef.current.on("call_rejected", (data: { call_id: string }) => {
      console.log("Call rejected:", data.call_id)
      if (activeCall?.callId === data.call_id) {
        endCall()
        alert("Call rejected")
      }
    })

    socketRef.current.on("call_ended", (data: { call_id: string }) => {
      console.log("Call ended:", data.call_id)
      if (activeCall?.callId === data.call_id) {
        endCall()
      }
    })

    socketRef.current.on("webrtc_offer", (data: any) => {
      if (incomingCall?.call_id === data.callId) {
        handleWebRTCOffer(data)
      }
    })

    socketRef.current.on("webrtc_answer", (data: any) => {
      if (activeCall?.callId === data.callId) {
        handleWebRTCAnswer(data)
      }
    })

    socketRef.current.on("ice_candidate", (data: any) => {
      if ((activeCall?.callId === data.callId || incomingCall?.call_id === data.callId) && 
          peerConnection) {
        handleNewICECandidate(data.candidate)
      }
    })

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
    }
  }, [])

  // Message receiving with contact verification
  useEffect(() => {
    if (!socketRef.current) return

    const handleNewMessage = (message: Message) => {
      // Verify message is for the currently selected contact
      if (
        selectedContact && 
        message.sender_id === selectedContact.id && 
        message.sender_type === selectedContact.type
      ) {
        setMessages(prev => [...prev, message])
        scrollToBottom()
      }
    }

    socketRef.current.on("new_message", handleNewMessage)

    return () => {
      if (socketRef.current) {
        socketRef.current.off("new_message", handleNewMessage)
      }
    }
  }, [selectedContact])

  // Fetch contacts based on user type
  useEffect(() => {
    const fetchContacts = async () => {
      try {
        setContactsLoading(true)
        const token = localStorage.getItem("access_token")
        const endpoint = userType === "patient" 
          ? "http://localhost:5000/get_doctors_by_patient"
          : "http://localhost:5000/get_patients_by_doctor"
        
        const response = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ id: userId }),
        })

        if (response.ok) {
          const data = await response.json()
          const contacts = userType === "patient" 
            ? data.doctors.map((d: any) => ({ 
                ...d, 
                type: "doctor",
                name: `Dr. ${d.name}` 
              }))
            : data.patients.map((p: any) => ({ 
                ...p, 
                type: "patient" 
              }))
          
          setContacts(contacts)
          
          // Auto-select first contact if available
          if (contacts.length > 0 && !selectedContact) {
            setSelectedContact(contacts[0])
          }
        }
      } catch (error) {
        console.error("Failed to fetch contacts:", error)
      } finally {
        setContactsLoading(false)
      }
    }

    fetchContacts()
  }, [userType, userId])

  // Fetch messages when contact changes
  const fetchMessages = useCallback(async () => {
    if (!selectedContact) return

    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch(
        `http://localhost:5000/api/chat/messages/${selectedContact.type}/${selectedContact.id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )

      if (response.ok) {
        const data = await response.json()
        setMessages(data)
        scrollToBottom()
      }
    } catch (error) {
      console.error("Failed to fetch messages:", error)
    }
  }, [selectedContact])

  useEffect(() => {
    if (selectedContact) {
      fetchMessages()
    }
  }, [selectedContact, fetchMessages])

  // Set up video streams when active call changes
  useEffect(() => {
    if (activeCall) {
      setupMedia()
    } else {
      cleanupMedia()
    }
  }, [activeCall])

  const scrollToBottom = () => {
    setTimeout(() => {
      if (scrollAreaRef.current) {
        scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
      }
    }, 100)
  }

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedContact) return

    setLoading(true)
    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch("http://localhost:5000/api/chat/messages/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          receiver_type: selectedContact.type,
          receiver_id: selectedContact.id,
          content: newMessage,
        }),
      })

      if (response.ok) {
        const newMsg: Message = await response.json()
        setNewMessage("")
        
        // Add message to local state immediately
        setMessages(prev => [
          ...prev, 
          {
            ...newMsg,
            sender_type: userType,
            sender_id: userId,
            content: newMessage,
            timestamp: new Date().toISOString(),
            read: false
          }
        ])
        
        scrollToBottom()
      }
    } catch (error) {
      console.error("Failed to send message:", error)
    } finally {
      setLoading(false)
    }
  }

  const initiateCall = async () => {
    if (!selectedContact) return

    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch("http://localhost:5000/api/chat/call/initiate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          callee_type: selectedContact.type,
          callee_id: selectedContact.id,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        console.log("Call initiated:", data.call_id)
        setActiveCall({ callId: data.call_id, status: "initiated" })
        createPeerConnection(data.call_id)
      }
    } catch (error) {
      console.error("Failed to initiate call:", error)
    }
  }

  const acceptCall = () => {
    if (!incomingCall) return
    
    if (socketRef.current) {
      socketRef.current.emit("accept_call", { call_id: incomingCall.call_id })
      setActiveCall({ callId: incomingCall.call_id, status: "ongoing" })
      setIncomingCall(null)
      createPeerConnection(incomingCall.call_id)
    }
  }

  const rejectCall = () => {
    if (!incomingCall) return
    
    if (socketRef.current) {
      socketRef.current.emit("reject_call", { call_id: incomingCall.call_id })
      setIncomingCall(null)
    }
  }

  const endCall = async () => {
    if (!activeCall) return

    try {
      const token = localStorage.getItem("access_token")
      await fetch(`http://localhost:5000/api/chat/call/end/${activeCall.callId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      })
    } catch (error) {
      console.error("Failed to end call:", error)
    } finally {
      cleanupMedia()
      setActiveCall(null)
      setIncomingCall(null)
    }
  }

  const setupMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      })
      setLocalStream(stream)
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream
      }
    } catch (err) {
      console.error("Error accessing media devices:", err)
    }
  }

  const cleanupMedia = () => {
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop())
      setLocalStream(null)
    }
    
    if (remoteStream) {
      remoteStream.getTracks().forEach(track => track.stop())
      setRemoteStream(null)
    }
    
    if (peerConnection) {
      peerConnection.close()
      setPeerConnection(null)
    }
    
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = null
    }
    
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = null
    }
  }

  const createPeerConnection = (callId: string) => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    })
    
    pc.onicecandidate = (event) => {
      if (event.candidate && socketRef.current) {
        const targetType = activeCall ? selectedContact?.type : incomingCall?.caller.type
        const targetId = activeCall ? selectedContact?.id : incomingCall?.caller.id
        
        if (!targetType || !targetId) return
        
        socketRef.current.emit("ice_candidate", {
          callId,
          candidate: event.candidate,
          target_type: targetType,
          target_id: targetId
        })
      }
    }
    
    pc.ontrack = (event) => {
      setRemoteStream(event.streams[0])
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = event.streams[0]
      }
    }
    
    setPeerConnection(pc)
    
    if (localStream) {
      localStream.getTracks().forEach(track => {
        pc.addTrack(track, localStream)
      })
    }
    
    return pc
  }

  const handleWebRTCOffer = async (data: any) => {
    if (!peerConnection) return
    
    try {
      await peerConnection.setRemoteDescription(
        new RTCSessionDescription(data.offer)
      )
      
      const answer = await peerConnection.createAnswer()
      await peerConnection.setLocalDescription(answer)
      
      if (socketRef.current) {
        socketRef.current.emit("webrtc_answer", {
          callId: data.callId,
          answer: answer,
          caller_type: data.caller_type,
          caller_id: data.caller_id
        })
      }
    } catch (err) {
      console.error("Error handling WebRTC offer:", err)
    }
  }

  const handleWebRTCAnswer = async (data: any) => {
    if (!peerConnection) return
    
    try {
      await peerConnection.setRemoteDescription(
        new RTCSessionDescription(data.answer)
      )
    } catch (err) {
      console.error("Error handling WebRTC answer:", err)
    }
  }

  const handleNewICECandidate = async (candidate: RTCIceCandidate) => {
    if (!peerConnection) return
    
    try {
      await peerConnection.addIceCandidate(
        new RTCIceCandidate(candidate)
      )
    } catch (err) {
      console.error("Error adding ICE candidate:", err)
    }
  }

  const createOffer = async () => {
    if (!peerConnection || !selectedContact) return
    
    try {
      const offer = await peerConnection.createOffer()
      await peerConnection.setLocalDescription(offer)
      
      if (socketRef.current) {
        socketRef.current.emit("webrtc_offer", {
          callId: activeCall?.callId,
          offer: offer,
          callee_type: selectedContact.type,
          callee_id: selectedContact.id
        })
      }
    } catch (err) {
      console.error("Error creating offer:", err)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px] relative">
      {/* Incoming Call Modal */}
      {incomingCall && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <Card className="w-96">
            <CardHeader>
              <CardTitle>Incoming Video Call</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-4">
                <Avatar className="mx-auto w-16 h-16">
                  <AvatarFallback>
                    {incomingCall.caller.type.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <p className="mt-2 text-lg font-medium">
                  {incomingCall.caller.type} #{incomingCall.caller.id}
                </p>
                <p className="text-gray-500">is calling you...</p>
              </div>
              
              <div className="flex justify-between mt-4">
                <Button 
                  variant="destructive" 
                  className="flex-1 mr-2"
                  onClick={rejectCall}
                >
                  Reject
                </Button>
                <Button 
                  variant="success"
                  className="flex-1 ml-2"
                  onClick={acceptCall}
                >
                  Accept
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Video Call Interface */}
      {activeCall && (
        <div className="fixed inset-0 bg-black z-50 flex flex-col">
          <div className="flex-1 relative">
            {/* Remote video */}
            <video 
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            
            {/* Local video */}
            {localStream && (
              <div className="absolute bottom-4 right-4 w-48 h-36 rounded-lg overflow-hidden shadow-lg border-2 border-white">
                <video 
                  ref={localVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            
            {/* Call controls */}
            <div className="absolute bottom-4 left-0 right-0 flex justify-center">
              <Button 
                variant="destructive" 
                className="rounded-full w-16 h-16"
                onClick={endCall}
              >
                <Phone className="h-8 w-8" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Contacts List */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Contacts</CardTitle>
        </CardHeader>
        <CardContent>
          {contactsLoading ? (
            <div className="flex justify-center items-center h-40">
              <p>Loading contacts...</p>
            </div>
          ) : contacts.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              {userType === "doctor" 
                ? "You haven't had appointments with any patients yet" 
                : "You haven't booked appointments with any doctors yet"}
            </p>
          ) : (
            <div className="space-y-2">
              {contacts.map(contact => (
                <div
                  key={`${contact.type}-${contact.id}`}
                  className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer ${
                    selectedContact?.id === contact.id 
                      ? "bg-blue-100 border border-blue-200" 
                      : "hover:bg-gray-50"
                  }`}
                  onClick={() => setSelectedContact(contact)}
                >
                  <Avatar>
                    <AvatarFallback>
                      {contact.name.split(" ").map(n => n[0]).join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="overflow-hidden">
                    <p className="font-medium truncate">{contact.name}</p>
                    <p className="text-sm text-gray-500 truncate">
                      {userType === "doctor" 
                        ? `Age: ${contact.age} • ${contact.gender}`
                        : contact.specialization}
                    </p>
                    <p className="text-xs text-gray-400">ID: {contact.id}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              {selectedContact
                ? `Chat with ${selectedContact.name} (ID: ${selectedContact.id})`
                : "Select a contact to start chatting"}
            </CardTitle>
            {selectedContact && !activeCall && (
              <div className="flex space-x-2">
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={initiateCall}
                  disabled={!!incomingCall}
                >
                  <Video className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="flex flex-col h-[500px]">
          {selectedContact ? (
            <>
              {/* Messages */}
              <ScrollArea className="flex-1 pr-4" ref={scrollAreaRef}>
                <div className="space-y-4">
                  {messages.length === 0 ? (
                    <div className="flex justify-center items-center h-full">
                      <p className="text-gray-500">No messages yet. Start the conversation!</p>
                    </div>
                  ) : (
                    messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${
                          message.sender_type === userType && message.sender_id === userId
                            ? "justify-end"
                            : "justify-start"
                        }`}
                      >
                        <div
                          className={`max-w-[70%] rounded-lg px-3 py-2 ${
                            message.sender_type === userType && message.sender_id === userId
                              ? "bg-blue-600 text-white"
                              : "bg-gray-100 text-gray-900"
                          }`}
                        >
                          <p>{message.content}</p>
                          <p className="text-xs mt-1 opacity-70">
                            {format(new Date(message.timestamp), "MMM d, yyyy HH:mm")}
                            <span className="ml-2">
                              (Sender: {message.sender_type}-{message.sender_id})
                            </span>
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>

              {/* Message Input */}
              <div className="flex space-x-2 mt-4">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Type your message..."
                  onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                  disabled={loading || !!incomingCall || !!activeCall}
                />
                <Button 
                  onClick={sendMessage} 
                  disabled={loading || !newMessage.trim() || !!incomingCall || !!activeCall}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              {contacts.length > 0 
                ? "Select a contact to start messaging" 
                : "No contacts available"}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}