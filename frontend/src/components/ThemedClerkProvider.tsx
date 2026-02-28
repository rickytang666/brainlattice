import { ClerkProvider } from '@clerk/clerk-react'
import { useTheme } from './ThemeProvider'
import { dark } from '@clerk/themes'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

export function ThemedClerkProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  
  const isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);

  if (!PUBLISHABLE_KEY) return <>{children}</>;

  return (
    <ClerkProvider 
      publishableKey={PUBLISHABLE_KEY} 
      afterSignOutUrl="/"
      appearance={{
        baseTheme: isDark ? dark : undefined,
        variables: { colorPrimary: '#069eb9' }
      }}
    >
      {children}
    </ClerkProvider>
  );
}
