// AIMETA P=主题组合函数_明暗主题切换管理|R=theme_toggle_persist|NR=不含UI组件|E=compose:useTheme|X=internal|A=useTheme函数|D=vue|S=dom,storage|RD=./README.ai
import { ref, onMounted, onUnmounted, computed } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

// Global reactive state for theme
const isDark = ref(false)
const themeMode = ref<ThemeMode>('system')
const isInitialized = ref(false)

// Storage keys - unified keys for consistency
const THEME_STORAGE_KEY = 'novel-theme-mode'
// Legacy keys for migration
const LEGACY_THEME_KEY = 'theme'
const LEGACY_SYSTEM_KEY = 'useSystemTheme'

// Track media query listener for cleanup
let mediaQueryListener: ((e: MediaQueryListEvent) => void) | null = null
let mediaQuery: MediaQueryList | null = null

/**
 * Get system preference for dark mode
 */
const getSystemPreference = (): boolean => {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

/**
 * Apply theme to document - unified DOM operations
 */
const applyTheme = (dark: boolean): void => {
  if (typeof document === 'undefined') return

  isDark.value = dark

  if (dark) {
    document.documentElement.setAttribute('data-theme', 'dark')
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.setAttribute('data-theme', 'light')
    document.documentElement.classList.remove('dark')
  }
}

/**
 * Resolve actual dark state from theme mode
 */
const resolveTheme = (mode: ThemeMode): boolean => {
  if (mode === 'system') {
    return getSystemPreference()
  }
  return mode === 'dark'
}

/**
 * Migrate legacy theme settings to new unified key
 */
const migrateLegacySettings = (): ThemeMode | null => {
  if (typeof localStorage === 'undefined') return null

  try {
    const legacySystemPref = localStorage.getItem(LEGACY_SYSTEM_KEY)
    const legacyTheme = localStorage.getItem(LEGACY_THEME_KEY)

    // If legacy system preference exists
    if (legacySystemPref === 'true') {
      // Clean up legacy keys
      localStorage.removeItem(LEGACY_SYSTEM_KEY)
      localStorage.removeItem(LEGACY_THEME_KEY)
      return 'system'
    }

    // If legacy theme exists
    if (legacyTheme && ['light', 'dark'].includes(legacyTheme)) {
      // Clean up legacy keys
      localStorage.removeItem(LEGACY_SYSTEM_KEY)
      localStorage.removeItem(LEGACY_THEME_KEY)
      return legacyTheme as ThemeMode
    }

    return null
  } catch {
    return null
  }
}

/**
 * Setup system preference change listener
 */
const setupSystemPreferenceListener = (): void => {
  if (typeof window === 'undefined') return

  // Clean up existing listener if any
  cleanupSystemPreferenceListener()

  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQueryListener = (e: MediaQueryListEvent) => {
    if (themeMode.value === 'system') {
      applyTheme(e.matches)
    }
  }
  mediaQuery.addEventListener('change', mediaQueryListener)
}

/**
 * Cleanup system preference change listener
 */
const cleanupSystemPreferenceListener = (): void => {
  if (mediaQuery && mediaQueryListener) {
    mediaQuery.removeEventListener('change', mediaQueryListener)
    mediaQueryListener = null
    mediaQuery = null
  }
}

/**
 * Initialize theme from storage or system preference
 */
const initializeTheme = (): void => {
  if (isInitialized.value) return

  try {
    // First try to migrate legacy settings
    const migratedMode = migrateLegacySettings()

    if (migratedMode) {
      themeMode.value = migratedMode
      // Save migrated setting to new key
      localStorage.setItem(THEME_STORAGE_KEY, migratedMode)
    } else {
      // Read from unified key
      const saved = localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null

      if (saved && ['light', 'dark', 'system'].includes(saved)) {
        themeMode.value = saved
      } else {
        themeMode.value = 'system'
      }
    }

    applyTheme(resolveTheme(themeMode.value))

    // Setup system preference listener
    setupSystemPreferenceListener()

    isInitialized.value = true
  } catch {
    // Silent fail in production, apply default theme
    applyTheme(false)
  }
}

/**
 * Set theme mode and persist to storage
 */
const setThemeMode = (mode: ThemeMode): void => {
  themeMode.value = mode
  applyTheme(resolveTheme(mode))

  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode)
    // Clean up legacy keys if they exist
    localStorage.removeItem(LEGACY_THEME_KEY)
    localStorage.removeItem(LEGACY_SYSTEM_KEY)
  } catch {
    // Silent fail in production
  }
}

/**
 * Toggle between light and dark (ignores system mode)
 */
const toggleTheme = (): void => {
  const newMode: ThemeMode = isDark.value ? 'light' : 'dark'
  setThemeMode(newMode)
}

/**
 * Cycle through theme modes: light -> dark -> system -> light
 */
const cycleTheme = (): void => {
  const modes: ThemeMode[] = ['light', 'dark', 'system']
  const currentIndex = modes.indexOf(themeMode.value)
  const nextIndex = (currentIndex + 1) % modes.length
  setThemeMode(modes[nextIndex])
}

/**
 * Theme composable for Vue components
 *
 * @example
 * ```vue
 * <script setup>
 * const { isDark, themeMode, toggleTheme, setThemeMode } = useTheme()
 * </script>
 *
 * <template>
 *   <button @click="toggleTheme">
 *     {{ isDark ? 'Switch to Light' : 'Switch to Dark' }}
 *   </button>
 * </template>
 * ```
 */
export function useTheme() {
  // Initialize on first use
  onMounted(() => {
    initializeTheme()
  })

  // Cleanup on unmount
  onUnmounted(() => {
    cleanupSystemPreferenceListener()
  })

  // Computed properties
  const themeModeLabel = computed(() => {
    switch (themeMode.value) {
      case 'light':
        return '浅色模式'
      case 'dark':
        return '深色模式'
      case 'system':
        return '跟随系统'
      default:
        return '未知'
    }
  })

  const themeIcon = computed(() => {
    switch (themeMode.value) {
      case 'light':
        return 'sun'
      case 'dark':
        return 'moon'
      case 'system':
        return 'computer'
      default:
        return 'sun'
    }
  })

  const isSystemMode = computed(() => themeMode.value === 'system')

  return {
    // State
    isDark,
    themeMode,
    isInitialized,

    // Computed
    themeModeLabel,
    themeIcon,
    isSystemMode,

    // Actions
    toggleTheme,
    cycleTheme,
    setThemeMode,
    initializeTheme,
    cleanupSystemPreferenceListener,
  }
}

// Export global functions for non-component usage
export {
  isDark,
  themeMode,
  toggleTheme,
  cycleTheme,
  setThemeMode,
  initializeTheme,
  cleanupSystemPreferenceListener,
}

// Default export
export default useTheme
