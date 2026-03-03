import { useUser, useAuth, SignIn } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, XCircle } from "lucide-react";
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export default function CliAuthRoute() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const [searchParams] = useSearchParams();
  const redirectUri = searchParams.get("redirect_uri");
  
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function handoffToCli() {
      if (!isLoaded || !user) return;
      if (!redirectUri) {
        setStatus("error");
        setErrorMessage("no redirect_uri provided. did you run 'brainlattice login'?");
        return;
      }

      try {
        const token = await getToken();
        
        const callbackUrl = new URL(redirectUri);
        callbackUrl.searchParams.set("user_id", user.id);
        if (token) {
          callbackUrl.searchParams.set("token", token);
        }
        
        // redirect to the cli server to show the custom success page
        window.location.assign(callbackUrl.toString());
      } catch (e: unknown) {
        setStatus("error");
        setErrorMessage(e instanceof Error ? e.message : "failed to handoff credentials to the cli");
      }
    }

    handoffToCli();
  }, [isLoaded, user, redirectUri, getToken]);

  if (!isLoaded) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // if user is not logged in, show the clerk sign in box. 
  if (!user) {
    return (
      <div className="flex flex-col h-screen w-full items-center justify-center bg-background p-4 animate-in fade-in duration-500">
        <div className="mb-10 text-center space-y-3">
          <div className="text-muted-foreground font-serif italic text-lg mb-4">brainlattice</div>
          <h1 className="text-3xl font-serif font-medium tracking-tight">cli authentication</h1>
          <p className="text-muted-foreground text-sm max-w-[380px] leading-relaxed">
            please sign in to your account to authorize the command line interface.
          </p>
        </div>
        <SignIn routing="hash" />
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background p-4 font-sans">
      <div className={cn(
        "flex flex-col items-center justify-center p-10 rounded-2xl border max-w-md w-full text-center space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700",
        status === "success" ? "border-emerald-500/10 bg-emerald-500/5" : "border-border bg-card shadow-sm"
      )}>
        {status === "processing" && (
          <>
            <Loader2 className="h-10 w-10 animate-spin text-muted-foreground mb-2" />
            <h2 className="text-2xl font-serif font-medium">linking your account...</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              please wait while we securely transmit your credentials to your local terminal session.
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="h-16 w-16 text-destructive/80 mb-2" />
            <h2 className="text-2xl font-serif font-medium text-destructive/90">authentication failed</h2>
            <p className="text-muted-foreground text-sm leading-relaxed">
              {errorMessage}
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
            >
              retry link
            </button>
          </>
        )}
      </div>
    </div>
  );
}
