"use client"

import { SideNav } from "@/components/layout/side-nav"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const router = useRouter()
    const [authorized, setAuthorized] = useState(false)

    useEffect(() => {
        const token = localStorage.getItem("token")
        if (!token) {
            router.push("/login")
        } else {
            setAuthorized(true)
        }
    }, [router])

    if (!authorized) {
        return null // Or a loading spinner
    }

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            <SideNav />
            <main className="flex-1 overflow-y-auto p-8">
                {children}
            </main>
        </div>
    )
}
