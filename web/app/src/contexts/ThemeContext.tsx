import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

const THEME_KEY = 'holkos_theme'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  isDark: boolean
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | null>(null)

function readStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'light'
  const stored = localStorage.getItem(THEME_KEY) as Theme | null
  return stored === 'dark' || stored === 'light' ? stored : 'light'
}

function applyThemeToDom(next: Theme) {
  const root = document.documentElement
  if (next === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
  try {
    localStorage.setItem(THEME_KEY, next)
  } catch (_) {}
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readStoredTheme)

  useEffect(() => {
    applyThemeToDom(theme)
  }, [theme])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])

  const toggleTheme = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark'
    applyThemeToDom(next)
    setThemeState(next)
  }, [theme])

  const isDark = theme === 'dark'

  return (
    <ThemeContext.Provider value={{ theme, isDark, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

const defaultTheme: ThemeContextType = {
  theme: 'light',
  isDark: false,
  setTheme: () => {},
  toggleTheme: () => {},
}

export function useTheme(): ThemeContextType {
  const ctx = useContext(ThemeContext)
  return ctx ?? defaultTheme
}
