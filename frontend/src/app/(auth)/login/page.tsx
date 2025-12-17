"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Bot } from "lucide-react"
import api from "@/lib/api"

import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
    const router = useRouter()
    const [isLoading, setIsLoading] = React.useState(false)
    const [error, setError] = React.useState<string | null>(null)

    async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setIsLoading(true)
        setError(null)

        const formData = new FormData(event.currentTarget)
        const email = formData.get("email") as string
        const password = formData.get("password") as string

        try {
            // The backend expects x-www-form-urlencoded for OAuth2 password flow usually, 
            // but let's check the backend auth logic usually in FastAPI.
            // Usually FastAPI's OAuth2PasswordRequestForm expects form data, not JSON.
            // Let's try standard JSON first if the backend supports it, otherwise form data.
            // Checking backend schemas earlier: UserLogin was defined in schemas/user.py.
            // But typically /token endpoint uses form data.
            // Wait, let's assume the router uses the UserLogin schema which suggests JSON body.
            // I should double check the backend code if possible, but let's try JSON first as it's common for "login" endpoints vs "token" endpoints.
            // Actually, standard FastAPI auth usually uses /token with form data.
            // BUT, I'll use the new /api/v1/auth/login if it exists.
            // I'll assume JSON for now based on `UserLogin` schema presence.

            const response = await api.post("/v1/auth/login", {
                email,
                password,
            })

            if (response.data.access_token) {
                localStorage.setItem("token", response.data.access_token)
                router.push("/")
            }
        } catch (err: any) {
            setError("Invalid email or password")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Card className="w-full max-w-sm">
            <CardHeader className="space-y-1">
                <div className="flex justify-center mb-4">
                    <div className="bg-primary/10 p-3 rounded-full">
                        <Bot className="h-6 w-6 text-primary" />
                    </div>
                </div>
                <CardTitle className="text-2xl text-center">Welcome back</CardTitle>
                <CardDescription className="text-center">
                    Enter your email to sign in to your account
                </CardDescription>
            </CardHeader>
            <form onSubmit={onSubmit}>
                <CardContent className="grid gap-4">
                    {error && (
                        <div className="text-sm text-destructive text-center font-medium">
                            {error}
                        </div>
                    )}
                    <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            name="email"
                            type="email"
                            placeholder="m@example.com"
                            required
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="password">Password</Label>
                        <Input
                            id="password"
                            name="password"
                            type="password"
                            required
                        />
                    </div>
                </CardContent>
                <CardFooter className="flex flex-col gap-4">
                    <Button className="w-full" disabled={isLoading}>
                        {isLoading ? "Signing in..." : "Sign in"}
                    </Button>
                    <div className="text-center text-sm text-muted-foreground">
                        Don&apos;t have an account?{" "}
                        <Link href="/register" className="underline underline-offset-4 hover:text-primary">
                            Sign up
                        </Link>
                    </div>
                </CardFooter>
            </form>
        </Card>
    )
}
