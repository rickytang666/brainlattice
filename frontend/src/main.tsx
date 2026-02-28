import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.tsx'
import { ThemeProvider, useTheme } from './components/ThemeProvider.tsx'
import { dark } from '@clerk/themes'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

// eslint-disable-next-line react-refresh/only-export-components
function ThemedClerkProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  
  const isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);

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
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <ThemedClerkProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemedClerkProvider>
    </ThemeProvider>
  </StrictMode>,
)
