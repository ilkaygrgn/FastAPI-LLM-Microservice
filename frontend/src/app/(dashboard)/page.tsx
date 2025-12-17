import { ChatWindow } from "@/components/chat/chat-window"

export default function DashboardPage() {
    return (
        <div className="h-full flex flex-col gap-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                <p className="text-muted-foreground">
                    Chat with your intelligent assistant utilizing RAG capabilities.
                </p>
            </div>
            <div className="flex-1 min-h-0">
                <ChatWindow />
            </div>
        </div>
    )
}
