import React from 'react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import { Bot, User } from 'lucide-react'

interface MessageBubbleProps {
    role: 'user' | 'assistant'
    content: string
    thoughts?: string[]
}

export function MessageBubble({ role, content, thoughts }: MessageBubbleProps) {
    return (
        <div
            className={cn(
                "flex w-full items-start gap-4 p-4",
                role === "assistant" ? "bg-muted/50" : "bg-background"
            )}
        >
            <div className={cn(
                "flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow",
                role === "assistant" ? "bg-primary text-primary-foreground border-primary" : "bg-background"
            )}>
                {role === "assistant" ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
            </div>
            <div className="flex-1 space-y-2 overflow-hidden">
                {thoughts && thoughts.length > 0 && (
                    <div className="mb-3 rounded-md border border-indigo-200 bg-indigo-50/50 p-3">
                        {(() => {
                            const agentNames = Array.from(new Set(thoughts.map(t => {
                                const match = t.match(/tool: (\w+)/);
                                return match ? match[1].replace(/_/g, ' ') : null;
                            }).filter(Boolean))).map(name =>
                                name?.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
                            );
                            const isRag = thoughts.some(t => t.includes("RAG: Retrieved"));

                            return (
                                <>
                                    {agentNames.length > 0 && (
                                        <div className="flex items-center gap-2 text-sm font-semibold text-indigo-700 mb-2">
                                            <Bot className="h-4 w-4" />
                                            <span>
                                                Answer prepared with {agentNames.join(', ')} Agent
                                            </span>
                                        </div>
                                    )}
                                    {isRag && (
                                        <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700 mb-2">
                                            <span className="bg-emerald-100 text-emerald-800 text-xs px-2 py-0.5 rounded border border-emerald-200">
                                                Used RAG
                                            </span>
                                        </div>
                                    )}
                                </>
                            );
                        })()}
                        <div className="space-y-1 pl-6 border-l-2 border-indigo-200 ml-1">
                            {thoughts.map((thought, idx) => (
                                <div key={idx} className="text-xs text-muted-foreground">
                                    {thought}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                <div className="prose break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-0">
                    <ReactMarkdown
                        components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            code: ({ className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '')
                                return match ? (
                                    <code className={className} {...props}>
                                        {children}
                                    </code>
                                ) : (
                                    <code className="bg-muted px-1 py-0.5 rounded font-mono text-sm" {...props}>
                                        {children}
                                    </code>
                                )
                            }
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                </div>
            </div>
        </div>
    )
}
