
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.tsx'
import { ThemeProvider, useTheme } from './components/ThemeProvider.tsx'
import { dark } from '@clerk/themes'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

function ThemedClerkProvider({ children }: { children: React.ReactNode }) {
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

createRoot(document.getElementById('root')!).render(
  <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
    <ThemedClerkProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemedClerkProvider>
  </ThemeProvider>,
)
