"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import { Loader2, AlertCircle, ArrowRight, Layers } from "lucide-react";
import Link from "next/link";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const processAuth = async () => {
      const code = searchParams.get("code");
      const errorParam = searchParams.get("error_description") || searchParams.get("error");
      const redirectTo = searchParams.get("redirectTo") || "/dashboard";

      if (errorParam) {
        if (isMounted) setErrorMsg(errorParam);
        return;
      }

      try {
        if (code) {
          // Exchange code for session in PKCE flow
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            console.error("Code exchange failed:", exchangeError);
            if (isMounted) setErrorMsg(exchangeError.message);
            return;
          }
        }

        // Check if session is established (works for PKCE or hash-fragment implicit flow)
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          if (isMounted) setErrorMsg(sessionError.message);
          return;
        }

        if (session) {
          router.replace(redirectTo);
          router.refresh();
        } else {
          // Wait briefly for Supabase onAuthStateChange listener to detect hash tokens
          const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (_event, currentSession) => {
              if (currentSession && isMounted) {
                subscription.unsubscribe();
                router.replace(redirectTo);
                router.refresh();
              }
            }
          );

          // Fallback timeout if no session is captured after 4 seconds
          setTimeout(() => {
            if (isMounted) {
              subscription.unsubscribe();
              router.replace(redirectTo);
            }
          }, 4000);
        }
      } catch (err) {
        console.error("Auth callback error:", err);
        if (isMounted) {
          setErrorMsg(err instanceof Error ? err.message : "Authentication failed.");
        }
      }
    };

    processAuth();

    return () => {
      isMounted = false;
    };
  }, [router, searchParams]);

  if (errorMsg) {
    return (
      <div className="w-full max-w-md rounded-2xl border border-zinc-800/80 bg-zinc-900/70 backdrop-blur-xl p-8 shadow-2xl text-center">
        <div className="h-12 w-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Authentication Failed</h2>
        <p className="text-sm text-zinc-400 mb-6 leading-relaxed">{errorMsg}</p>
        <Link
          href="/login"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold text-white transition"
        >
          <span>Return to Sign In</span>
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md rounded-2xl border border-zinc-800/80 bg-zinc-900/70 backdrop-blur-xl p-8 shadow-2xl text-center">
      <div className="h-14 w-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-5 relative">
        <div className="absolute inset-0 rounded-2xl bg-indigo-500/10 animate-ping" />
        <Layers className="h-7 w-7 text-indigo-400 relative z-10" />
      </div>
      <h2 className="text-xl font-bold text-white mb-2 tracking-tight">
        Completing Google Sign-In
      </h2>
      <p className="text-sm text-zinc-400 mb-6">
        Setting up your secure session and preparing your opportunity feed...
      </p>
      <div className="flex items-center justify-center gap-2 text-xs text-indigo-400 font-medium">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Authenticating...</span>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />

      <Suspense
        fallback={
          <div className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
            <span>Loading...</span>
          </div>
        }
      >
        <CallbackHandler />
      </Suspense>
    </div>
  );
}
