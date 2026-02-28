import { useAuth } from "@clerk/clerk-react";

/**
 * A wrapper around Clerk's useAuth that gracefully handles cases where
 * the Clerk Publishable Key is missing (e.g. for local "Quick Run" development).
 */
export function useSafeAuth() {
  if (!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY) {
    return { 
      userId: null, 
      isLoaded: true,
      isSignedIn: false
    };
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  return useAuth();
}
