<!-- AIMETA P=设置页_用户设置|R=用户设置表单|NR=不含管理员设置|E=route:/settings#component:SettingsView|X=ui|A=设置表单|D=vue|S=dom,net|RD=./README.ai -->
<template>
  <div class="settings-page">
    <!-- Decorative background -->
    <div class="settings-bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-paper-texture"></div>
    </div>

    <!-- Back button -->
    <div class="settings-back">
      <router-link to="/" class="back-link">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        <span>返回</span>
      </router-link>
    </div>

    <!-- Main content container -->
    <div class="settings-container">
      <!-- Sidebar navigation - Book index style -->
      <aside class="settings-sidebar">
        <!-- Book spine decoration -->
        <div class="sidebar-spine"></div>

        <div class="sidebar-content">
          <!-- Header with ornament -->
          <div class="sidebar-header">
            <div class="header-ornament">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h2 class="sidebar-title">设置</h2>
          </div>

          <!-- Navigation items -->
          <nav class="sidebar-nav">
            <ul class="nav-list">
              <!-- Theme settings -->
              <li
                :class="['nav-item', { 'nav-item-active': activeSection === 'theme' }]"
                @click="activeSection = 'theme'"
              >
                <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <span class="nav-text">外观主题</span>
                <span class="nav-badge" v-if="isDark">暗色</span>
              </li>

              <!-- LLM settings -->
              <li
                :class="['nav-item', { 'nav-item-active': activeSection === 'llm' }]"
                @click="activeSection = 'llm'"
              >
                <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span class="nav-text">LLM 配置</span>
              </li>
            </ul>
          </nav>

          <!-- Decorative footer -->
          <div class="sidebar-footer">
            <span class="footer-line"></span>
            <svg class="footer-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span class="footer-line"></span>
          </div>
        </div>
      </aside>

      <!-- Main settings area -->
      <main class="settings-main">
        <!-- Theme settings section -->
        <section v-if="activeSection === 'theme'" class="settings-section">
          <div class="section-card">
            <!-- Paper texture -->
            <div class="card-texture"></div>

            <div class="section-header">
              <h3 class="section-title">外观主题</h3>
              <p class="section-desc">根据您的偏好选择明亮或暗色主题</p>
            </div>

            <div class="theme-options">
              <!-- Light theme option -->
              <div
                :class="['theme-option', { 'theme-option-active': !isDark }]"
                @click="setTheme(false)"
              >
                <div class="theme-preview theme-preview-light">
                  <div class="preview-header"></div>
                  <div class="preview-sidebar"></div>
                  <div class="preview-content">
                    <div class="preview-line"></div>
                    <div class="preview-line preview-line-short"></div>
                  </div>
                </div>
                <div class="theme-info">
                  <span class="theme-name">明亮模式</span>
                  <span class="theme-desc">温暖纸张风格</span>
                </div>
                <div class="theme-check" v-if="!isDark">
                  <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>

              <!-- Dark theme option -->
              <div
                :class="['theme-option', { 'theme-option-active': isDark }]"
                @click="setTheme(true)"
              >
                <div class="theme-preview theme-preview-dark">
                  <div class="preview-header"></div>
                  <div class="preview-sidebar"></div>
                  <div class="preview-content">
                    <div class="preview-line"></div>
                    <div class="preview-line preview-line-short"></div>
                  </div>
                </div>
                <div class="theme-info">
                  <span class="theme-name">暗色模式</span>
                  <span class="theme-desc">午夜书房风格</span>
                </div>
                <div class="theme-check" v-if="isDark">
                  <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path fill-rule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clip-rule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            <!-- System preference option -->
            <div class="system-theme-option">
              <label class="system-toggle">
                <input
                  type="checkbox"
                  :checked="isSystemMode"
                  @change="toggleSystemTheme"
                />
                <span class="toggle-slider"></span>
              </label>
              <div class="system-info">
                <span class="system-label">跟随系统</span>
                <span class="system-desc">自动根据系统设置切换主题</span>
              </div>
            </div>
          </div>
        </section>

        <!-- LLM settings section -->
        <section v-if="activeSection === 'llm'" class="settings-section">
          <LLMSettings />
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTheme } from '@/composables/useTheme'
import type { ThemeMode } from '@/composables/useTheme'
import LLMSettings from '@/components/LLMSettings.vue'

// Active section state
const activeSection = ref<'theme' | 'llm'>('theme')

// Use unified theme composable
const { isDark, themeMode, isSystemMode, setThemeMode } = useTheme()

const setTheme = (dark: boolean) => {
  setThemeMode(dark ? 'dark' : 'light')
}

const toggleSystemTheme = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    setThemeMode('system')
  } else {
    // Revert to current visual state as explicit mode
    setThemeMode(isDark.value ? 'dark' : 'light')
  }
}
</script>

<style scoped>
/* Settings Page Container */
.settings-page {
  min-height: 100vh;
  padding: var(--novel-space-4);
  background: var(--novel-surface-dim);
  position: relative;
  overflow-x: hidden;
}

/* Background decorations */
.settings-bg-decoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.4;
}

.bg-circle-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, var(--novel-primary-container) 0%, transparent 70%);
  top: -200px;
  right: -100px;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, var(--novel-secondary-container) 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
}

.bg-paper-texture {
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.3;
}

/* Back button */
.settings-back {
  position: absolute;
  top: var(--novel-space-4);
  left: var(--novel-space-4);
  z-index: 10;
}

.back-link {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-2) var(--novel-space-4);
  color: var(--novel-on-surface-variant);
  text-decoration: none;
  font-size: var(--novel-text-label);
  font-weight: 500;
  border-radius: var(--novel-radius-md);
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.back-link:hover {
  background: var(--novel-surface-container);
  color: var(--novel-on-surface);
}

/* Main container */
.settings-container {
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  padding-top: var(--novel-space-16);
  gap: var(--novel-space-6);
  position: relative;
}

@media (min-width: 768px) {
  .settings-container {
    flex-direction: row;
  }
}

/* Sidebar - Book index style */
.settings-sidebar {
  width: 100%;
  display: flex;
  background: var(--novel-surface);
  border-radius: var(--novel-radius-lg);
  box-shadow: var(--novel-shadow-md);
  overflow: hidden;
  position: relative;
}

@media (min-width: 768px) {
  .settings-sidebar {
    width: 260px;
    flex-shrink: 0;
  }
}

.sidebar-spine {
  width: 12px;
  background: linear-gradient(180deg, var(--novel-primary) 0%, var(--novel-primary-dark) 100%);
  flex-shrink: 0;
}

.sidebar-content {
  flex: 1;
  padding: var(--novel-space-6);
  position: relative;
}

.sidebar-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.4;
  pointer-events: none;
}

.sidebar-header {
  position: relative;
  margin-bottom: var(--novel-space-6);
}

.header-ornament {
  display: flex;
  justify-content: center;
  margin-bottom: var(--novel-space-3);
  color: var(--novel-primary);
}

.sidebar-title {
  font-family: var(--novel-font-heading);
  font-size: var(--novel-text-title);
  font-weight: 600;
  color: var(--novel-on-surface);
  text-align: center;
  margin: 0;
}

/* Navigation */
.sidebar-nav {
  position: relative;
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-2);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--novel-space-3);
  padding: var(--novel-space-3) var(--novel-space-4);
  border-radius: var(--novel-radius-md);
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
  position: relative;
}

.nav-item:hover {
  background: var(--novel-surface-container);
}

.nav-item-active {
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
}

.nav-item-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 60%;
  background: var(--novel-primary);
  border-radius: 0 var(--novel-radius-sm) var(--novel-radius-sm) 0;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-text {
  flex: 1;
  font-size: var(--novel-text-body);
  font-weight: 500;
}

.nav-badge {
  font-size: var(--novel-text-caption);
  padding: var(--novel-space-1) var(--novel-space-2);
  background: var(--novel-surface-container-high);
  border-radius: var(--novel-radius-full);
  color: var(--novel-on-surface-variant);
}

/* Sidebar footer ornament */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-3);
  margin-top: var(--novel-space-8);
  color: var(--novel-on-surface-variant);
  opacity: 0.5;
  position: relative;
}

.footer-line {
  width: 40px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--novel-outline), transparent);
}

.footer-icon {
  width: 20px;
  height: 20px;
}

/* Main settings area */
.settings-main {
  flex: 1;
  min-width: 0;
}

.settings-section {
  animation: section-appear 0.3s var(--novel-easing-emphasized);
}

@keyframes section-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Section card */
.section-card {
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  box-shadow: var(--novel-shadow-md);
  padding: var(--novel-space-8);
  position: relative;
  overflow: hidden;
}

.card-texture {
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.4;
  pointer-events: none;
}

.section-header {
  margin-bottom: var(--novel-space-8);
  position: relative;
}

.section-title {
  font-family: var(--novel-font-heading);
  font-size: var(--novel-text-headline);
  font-weight: 600;
  color: var(--novel-on-surface);
  margin: 0 0 var(--novel-space-2);
}

.section-desc {
  font-size: var(--novel-text-body);
  color: var(--novel-on-surface-variant);
  margin: 0;
}

/* Theme options */
.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--novel-space-4);
  margin-bottom: var(--novel-space-8);
  position: relative;
}

.theme-option {
  position: relative;
  padding: var(--novel-space-4);
  border: 2px solid var(--novel-outline-variant);
  border-radius: var(--novel-radius-lg);
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.theme-option:hover {
  border-color: var(--novel-primary);
  background: var(--novel-surface-container);
}

.theme-option-active {
  border-color: var(--novel-primary);
  background: var(--novel-primary-container);
}

/* Theme preview mock */
.theme-preview {
  aspect-ratio: 16 / 10;
  border-radius: var(--novel-radius-md);
  margin-bottom: var(--novel-space-3);
  overflow: hidden;
  position: relative;
  display: grid;
  grid-template-columns: 60px 1fr;
  grid-template-rows: 20px 1fr;
}

.theme-preview-light {
  background: #FFFDF8;
  border: 1px solid #E7E5E0;
}

.theme-preview-dark {
  background: #1C1A17;
  border: 1px solid #3D3A36;
}

.preview-header {
  grid-column: 1 / -1;
}

.theme-preview-light .preview-header {
  background: #F5F1E8;
}

.theme-preview-dark .preview-header {
  background: #252320;
}

.preview-sidebar {
  background: linear-gradient(180deg, var(--novel-primary) 0%, var(--novel-primary-dark) 100%);
}

.theme-preview-dark .preview-sidebar {
  background: linear-gradient(180deg, #F59E0B 0%, #D97706 100%);
}

.preview-content {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-line {
  height: 4px;
  border-radius: 2px;
}

.theme-preview-light .preview-line {
  background: #D6D3CD;
}

.theme-preview-dark .preview-line {
  background: #57534E;
}

.preview-line-short {
  width: 60%;
}

.theme-info {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-1);
}

.theme-name {
  font-size: var(--novel-text-body);
  font-weight: 600;
  color: var(--novel-on-surface);
}

.theme-desc {
  font-size: var(--novel-text-caption);
  color: var(--novel-on-surface-variant);
}

.theme-check {
  position: absolute;
  top: var(--novel-space-3);
  right: var(--novel-space-3);
  color: var(--novel-primary);
}

/* System theme toggle */
.system-theme-option {
  display: flex;
  align-items: center;
  gap: var(--novel-space-4);
  padding: var(--novel-space-4);
  background: var(--novel-surface-container);
  border-radius: var(--novel-radius-md);
  position: relative;
}

.system-toggle {
  position: relative;
  width: 48px;
  height: 26px;
  flex-shrink: 0;
}

.system-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--novel-outline);
  border-radius: var(--novel-radius-full);
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  top: 3px;
  background: var(--novel-surface);
  border-radius: 50%;
  transition: transform var(--novel-duration-fast) var(--novel-easing-standard);
  box-shadow: var(--novel-shadow-sm);
}

.system-toggle input:checked + .toggle-slider {
  background: var(--novel-primary);
}

.system-toggle input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

.system-info {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-1);
}

.system-label {
  font-size: var(--novel-text-body);
  font-weight: 500;
  color: var(--novel-on-surface);
}

.system-desc {
  font-size: var(--novel-text-caption);
  color: var(--novel-on-surface-variant);
}

/* Dark mode adjustments */
:root[data-theme="dark"] .settings-sidebar,
:root[data-theme="dark"] .section-card {
  background: var(--novel-surface-container);
}

:root[data-theme="dark"] .sidebar-content::before,
:root[data-theme="dark"] .card-texture {
  opacity: 0.2;
}

:root[data-theme="dark"] .bg-circle-1,
:root[data-theme="dark"] .bg-circle-2 {
  opacity: 0.2;
}

/* Responsive */
@media (max-width: 640px) {
  .settings-page {
    padding: var(--novel-space-3);
  }

  .settings-container {
    padding-top: var(--novel-space-12);
  }

  .section-card {
    padding: var(--novel-space-6);
  }

  .theme-options {
    grid-template-columns: 1fr;
  }
}
</style>
