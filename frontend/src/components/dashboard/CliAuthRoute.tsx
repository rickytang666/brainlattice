import { useUser, useAuth, SignIn } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
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
        
        // ping the local cli server with the user credentials
        const url = new URL(redirectUri);
        url.searchParams.set("user_id", user.id);
        if (token) {
          url.searchParams.set("token", token);
        }
        
        await fetch(url.toString(), { mode: 'no-cors' });
        
        setStatus("success");
      } catch (e: any) {
        setStatus("error");
        setErrorMessage(e.message || "failed to handoff credentials to the cli");
      }
    }

    handoffToCli();
  }, [isLoaded, user, redirectUri]);

  if (!isLoaded) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // if user is not logged in, show the clerk sign in box. 
  // after they sign in, this component will re-render with `user` populated.
  if (!user) {
    return (
      <div className="flex flex-col h-screen w-full items-center justify-center bg-background p-4">
        <div className="mb-8 text-center space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">cli authentication</h1>
          <p className="text-muted-foreground text-sm max-w-[400px]">
            please sign in to your brainlattice account to authorize the command line interface.
          </p>
        </div>
        <SignIn routing="hash" />
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background p-4">
      <div className={cn(
        "flex flex-col items-center justify-center p-8 rounded-xl border max-w-md w-full text-center space-y-4 shadow-sm",
        status === "success" ? "border-emerald-500/20 bg-emerald-500/5" : "",
        status === "error" ? "border-destructive/20 bg-destructive/5" : "",
        status === "processing" ? "border-border bg-card" : ""
      )}>
        {status === "processing" && (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-2" />
            <h2 className="text-xl font-semibold">authenticating your cli...</h2>
            <p className="text-sm text-muted-foreground">
              please wait while we hand off your credentials to your local terminal.
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle2 className="h-16 w-16 text-emerald-500 mb-2" />
            <h2 className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">auth successful!</h2>
            <p className="text-muted-foreground">
              your browser has successfully securely shared your session with the brainlattice cli.
            </p>
            <div className="mt-4 px-4 py-2 bg-background border rounded-lg text-sm font-mono text-foreground">
              you can now safely close this tab and return to your terminal.
            </div>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="h-16 w-16 text-destructive mb-2" />
            <h2 className="text-2xl font-bold text-destructive">authentication failed</h2>
            <p className="text-muted-foreground">
              {errorMessage}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
