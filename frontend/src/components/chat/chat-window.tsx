"use client"

import * as React from "react"
import { Send, Plus, Upload } from "lucide-react"
import { MessageBubble } from "./message-bubble"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

interface Message {
    role: "user" | "assistant"
    content: string
    thoughts?: string[]
}

export function ChatWindow() {
    const [messages, setMessages] = React.useState<Message[]>([])
    const [input, setInput] = React.useState("")
    const [isLoading, setIsLoading] = React.useState(false)
    // Simple session ID persistence for this demo
    const [sessionId, setSessionId] = React.useState(() => typeof window !== 'undefined' ? (localStorage.getItem('sessionId') || Math.random().toString(36).substring(7)) : Math.random().toString(36).substring(7))
    const [useRag, setUseRag] = React.useState(false) // Disabled by default
    const [isUploading, setIsUploading] = React.useState(false)
    const fileInputRef = React.useRef<HTMLInputElement>(null)

    React.useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('sessionId', sessionId)
        }
    }, [sessionId])

    const handleNewChat = () => {
        const newSessionId = Math.random().toString(36).substring(7)
        setSessionId(newSessionId)
        setMessages([])
        if (typeof window !== 'undefined') {
            localStorage.setItem('sessionId', newSessionId)
        }
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return

        const file = e.target.files[0]
        const formData = new FormData()
        formData.append("file", file)

        setIsUploading(true)
        try {
            // Upload to backend
            const response = await fetch("/api/v1/llm/upload-document", {
                method: "POST",
                body: formData,
            })

            if (!response.ok) throw new Error("Upload failed")

            // Show system message
            setMessages(prev => [...prev, {
                role: "assistant",
                content: `📄 **File Uploaded:** ${file.name}\n\nThe document is processed and ready for RAG.`,
                thoughts: []
            }])
            setUseRag(true) // Auto-enable RAG on upload

        } catch (error) {
            console.error(error)
            setMessages(prev => [...prev, {
                role: "assistant",
                content: `❌ **Upload Failed:** Could not upload ${file.name}.`,
                thoughts: []
            }])
        } finally {
            setIsUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ""
        }
    }

    async function sendMessage(e?: React.FormEvent) {
        if (e) e.preventDefault()
        if (!input.trim() || isLoading) return

        const userMessage = input.trim()
        setInput("")
        setMessages(prev => [...prev, { role: "user", content: userMessage }])
        setIsLoading(true)

        // Add placeholder for assistant
        setMessages(prev => [...prev, { role: "assistant", content: "", thoughts: [] }])

        try {
            const token = localStorage.getItem("token")
            const response = await fetch("/api/v1/llm/chat?enable_tools=true", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: sessionId,
                    use_rag: useRag
                })
            })

            if (!response.ok) {
                throw new Error("Failed to send message")
            }

            if (!response.body) return

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let assistantMessage = ""
            let currentThoughts: string[] = []
            let buffer = ""

            while (true) {
                const { value, done } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value, { stream: true })
                buffer += chunk

                const lines = buffer.split("\n")
                // Keep the last distinct part as it might be incomplete
                buffer = lines.pop() || ""

                let stateUpdated = false

                for (const line of lines) {
                    if (!line.trim()) continue
                    try {
                        const data = JSON.parse(line)
                        // console.log("DEBUG: Parsed stream data:", data) // Uncomment to debug raw stream
                        if (data.type === "thought") {
                            console.log("DEBUG: Thought received:", data.content)
                            currentThoughts.push(data.content)
                            stateUpdated = true
                        } else if (data.type === "text") {
                            assistantMessage += data.content
                            stateUpdated = true
                        }
                    } catch (err) {
                        console.error("Error parsing JSON stream:", err, "Line:", line)
                    }
                }

                if (stateUpdated) {
                    console.log("DEBUG: Updating state with thoughts:", currentThoughts)
                    setMessages(prev => {
                        const newMessages = [...prev]
                        newMessages[newMessages.length - 1] = {
                            role: "assistant",
                            content: assistantMessage,
                            thoughts: [...currentThoughts]
                        }
                        return newMessages
                    })
                }
            }

        } catch (error) {
            console.error("Chat error:", error)
            setMessages(prev => {
                const newMessages = [...prev]
                newMessages[newMessages.length - 1] = { role: "assistant", content: "Error: Failed to get response." }
                return newMessages
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="flex bg-background h-[calc(100vh-4rem)] flex-col rounded-xl border shadow-sm overflow-hidden">
            <div className="flex items-center justify-between border-b p-4 bg-muted/20">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">Chat Session</span>
                    <span className="text-xs text-muted-foreground font-mono bg-muted px-2 py-0.5 rounded">{sessionId}</span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="rag-toggle"
                            className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                            checked={useRag}
                            onChange={(e) => setUseRag(e.target.checked)}
                        />
                        <Label htmlFor="rag-toggle" className="cursor-pointer">Use RAG</Label>
                    </div>

                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        onChange={handleFileUpload}
                        accept=".txt,.md,.pdf"
                    />
                    <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
                        <Upload className="mr-2 h-4 w-4" />
                        {isUploading ? "Uploading..." : "Upload Doc"}
                    </Button>

                    <Button variant="outline" size="sm" onClick={handleNewChat}>
                        <Plus className="mr-2 h-4 w-4" /> New Chat
                    </Button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
                {messages.length === 0 && (
                    <div className="flex h-full flex-col items-center justify-center text-muted-foreground opacity-50">
                        <p className="mb-2 text-lg font-medium">No messages yet</p>
                        <p className="text-sm">Start a conversation with the AI assistant</p>
                    </div>
                )}
                {messages.map((msg, index) => (
                    <MessageBubble key={index} role={msg.role} content={msg.content} thoughts={msg.thoughts} />
                ))}
                {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
                    <div className="flex w-full items-start gap-4 p-4 bg-muted/50 opacity-50">
                        <div className="text-sm animate-pulse">Thinking...</div>
                    </div>
                )}
            </div>

            <div className="border-t p-4 bg-background">
                <form onSubmit={sendMessage} className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your message..."
                        disabled={isLoading}
                        className="flex-1"
                    />
                    <Button type="submit" disabled={isLoading || !input.trim()}>
                        <Send className="h-4 w-4" />
                    </Button>
                </form>
            </div>
        </div>
    )
}
