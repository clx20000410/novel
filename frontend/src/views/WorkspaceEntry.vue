<!-- AIMETA P=工作区入口_应用主入口|R=入口导航|NR=不含具体功能|E=route:/#component:WorkspaceEntry|X=ui|A=入口页|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="workspace-entry">
    <!-- Decorative background -->
    <div class="entry-bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-bookshelf"></div>
    </div>

    <!-- Update Log Modal (Scroll Style) -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="novel-dialog-overlay" @click.self="closeModal">
          <div class="update-log-modal">
            <!-- Scroll decorations -->
            <div class="scroll-rod scroll-rod-top"></div>
            <div class="scroll-rod scroll-rod-bottom"></div>

            <!-- Content -->
            <div class="scroll-content">
              <!-- Header -->
              <div class="scroll-header">
                <div class="novel-divider-ornament">
                  <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <h1 class="novel-headline text-center mt-4">更新日志</h1>
              </div>

              <!-- Community Section -->
              <div v-if="communityLog" class="community-section">
                <div class="prose max-w-none prose-sm" v-html="renderMarkdown(communityLog.content)"></div>
              </div>

              <!-- Timeline Content -->
              <div class="timeline-section">
                <div class="timeline-list">
                  <div v-for="(log, index) in filteredUpdateLogs" :key="log.id" class="timeline-item">
                    <!-- Timeline connector -->
                    <div v-if="index < filteredUpdateLogs.length - 1" class="timeline-connector"></div>

                    <!-- Timeline dot -->
                    <div class="timeline-dot"></div>

                    <!-- Content -->
                    <div class="timeline-content">
                      <time class="novel-caption">
                        {{ new Date(log.created_at).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) }}
                      </time>
                      <div class="timeline-card">
                        <div class="prose max-w-none prose-sm" v-html="renderMarkdown(log.content)"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Footer Actions -->
              <div class="scroll-footer">
                <button @click="hideModalToday" class="novel-btn novel-btn-ghost">
                  今日不再显示
                </button>
                <button @click="closeModal" class="novel-btn novel-btn-filled">
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Top Right Actions -->
    <div class="entry-actions">
      <router-link to="/settings" class="entry-action-btn">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span>设置</span>
      </router-link>
      <button @click="handleLogout" class="entry-action-btn">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        <span>退出</span>
      </button>
    </div>

    <!-- Main Content -->
    <div class="entry-content">
      <div class="entry-header">
        <!-- Decorative ornament -->
        <div class="header-ornament">
          <span class="ornament-wing"></span>
          <svg class="ornament-quill" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.707 5.293a1 1 0 010 1.414l-1.414 1.414a1 1 0 01-1.414 0L14 4.243 4.929 13.314a2 2 0 00-.499.838l-1.414 4.243a1 1 0 001.213 1.213l4.243-1.414a2 2 0 00.838-.499l9.071-9.071-3.879-3.879-1.414 1.414a1 1 0 11-1.414-1.414L13.414 3l1.293-1.293a1 1 0 011.414 0l4.586 4.586z" />
          </svg>
          <span class="ornament-wing"></span>
        </div>

        <h1 class="novel-display entry-title">
          拯救小说家
        </h1>
        <p class="novel-subtitle entry-subtitle">
          从一个新灵感开始，或继续打磨你的世界
        </p>
      </div>

      <!-- Mode Selection Cards -->
      <div class="entry-cards">
        <!-- Inspiration Mode Card -->
        <div @click="goToInspiration" class="entry-card entry-card-inspiration">
          <div class="card-bookmark">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </div>
          <div class="card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h2 class="card-title">灵感模式</h2>
          <p class="card-desc">没有头绪？让AI通过对话式引导，帮你构建故事的雏形。</p>
          <div class="card-action">
            <span>开始创作</span>
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>

        <!-- Novel Workspace Card -->
        <div @click="goToWorkspace" class="entry-card entry-card-workspace">
          <div class="card-bookmark card-bookmark-secondary">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
          </div>
          <div class="card-icon card-icon-secondary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h2 class="card-title card-title-secondary">小说工作台</h2>
          <p class="card-desc">查看、编辑和管理你所有的小说项目工程。</p>
          <div class="card-action card-action-secondary">
            <span>进入书房</span>
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Decorative footer ornament -->
      <div class="entry-footer-ornament">
        <span class="footer-line"></span>
        <svg class="footer-icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
        </svg>
        <span class="footer-line"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { marked } from 'marked'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getLatestUpdates } from '../api/updates'
import type { UpdateLog } from '../api/updates'

marked.setOptions({
  gfm: true,
  breaks: true
})

const renderMarkdown = (md: string) => marked.parse(md)

const router = useRouter()
const authStore = useAuthStore()

const showModal = ref(false)
const updateLogs = ref<UpdateLog[]>([])

// 查找包含"交流群"的日志
const communityLog = computed(() => {
  return updateLogs.value.find(log => /交流群/.test(log.content))
})

// 过滤掉包含"交流群"的日志，用于时间线显示
const filteredUpdateLogs = computed(() => {
  if (!communityLog.value) {
    return updateLogs.value
  }
  return updateLogs.value.filter(log => log.id !== communityLog.value!.id)
})

onMounted(async () => {
  const hideUntil = localStorage.getItem('hideAnnouncement')
  if (hideUntil !== new Date().toDateString()) {
    try {
      updateLogs.value = await getLatestUpdates()
      if (updateLogs.value.length > 0) {
        showModal.value = true
      }
    } catch (error) {
      console.error('Failed to fetch update logs:', error)
    }
  }
})

const closeModal = () => {
  showModal.value = false
}

const hideModalToday = () => {
  localStorage.setItem('hideAnnouncement', new Date().toDateString())
  closeModal()
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const goToInspiration = () => {
  router.push('/inspiration')
}

const goToWorkspace = () => {
  router.push('/workspace')
}
</script>

<style scoped>
.workspace-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--novel-space-6);
  background: var(--novel-surface-dim);
  position: relative;
  overflow: hidden;
}

/* Background decorations */
.entry-bg-decoration {
  position: absolute;
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

.bg-bookshelf {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120px;
  background: linear-gradient(180deg, transparent 0%, var(--novel-surface-container) 100%);
  opacity: 0.5;
}

/* Top actions */
.entry-actions {
  position: absolute;
  top: var(--novel-space-4);
  right: var(--novel-space-4);
  display: flex;
  gap: var(--novel-space-2);
}

.entry-action-btn {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-2) var(--novel-space-4);
  background: transparent;
  color: var(--novel-on-surface-variant);
  border: none;
  border-radius: var(--novel-radius-md);
  font-size: var(--novel-text-label);
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.entry-action-btn:hover {
  background: var(--novel-surface-container);
  color: var(--novel-on-surface);
}

/* Main content */
.entry-content {
  width: 100%;
  max-width: 900px;
  text-align: center;
  animation: content-appear 0.8s var(--novel-easing-emphasized);
}

@keyframes content-appear {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Header */
.entry-header {
  margin-bottom: var(--novel-space-12);
}

.header-ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-4);
  margin-bottom: var(--novel-space-6);
  color: var(--novel-primary);
}

.ornament-wing {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--novel-primary), transparent);
}

.ornament-quill {
  width: 32px;
  height: 32px;
}

.entry-title {
  color: var(--novel-on-surface);
  margin-bottom: var(--novel-space-3);
}

.entry-subtitle {
  color: var(--novel-on-surface-variant);
}

/* Cards */
.entry-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--novel-space-6);
  max-width: 720px;
  margin: 0 auto var(--novel-space-12);
}

@media (max-width: 640px) {
  .entry-cards {
    grid-template-columns: 1fr;
  }
}

.entry-card {
  position: relative;
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  padding: var(--novel-space-8);
  box-shadow: var(--novel-shadow-md);
  cursor: pointer;
  transition: all var(--novel-duration-normal) var(--novel-easing-emphasized);
  overflow: hidden;
}

.entry-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.3;
  pointer-events: none;
}

.entry-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--novel-shadow-xl);
}

/* Bookmark decoration */
.card-bookmark {
  position: absolute;
  top: -4px;
  right: var(--novel-space-6);
  color: var(--novel-primary);
  opacity: 0.8;
  transition: transform var(--novel-duration-fast) var(--novel-easing-standard);
}

.card-bookmark-secondary {
  color: var(--novel-secondary);
}

.entry-card:hover .card-bookmark {
  transform: translateY(4px);
}

/* Card icon */
.card-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--novel-space-4);
  padding: var(--novel-space-4);
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
  border-radius: var(--novel-radius-lg);
  transition: transform var(--novel-duration-normal) var(--novel-easing-bounce);
}

.card-icon-secondary {
  background: var(--novel-secondary-container);
  color: var(--novel-on-secondary-container);
}

.entry-card:hover .card-icon {
  transform: scale(1.1);
}

.card-icon svg {
  width: 100%;
  height: 100%;
}

/* Card content */
.card-title {
  font-family: var(--novel-font-heading);
  font-size: var(--novel-text-title);
  font-weight: 600;
  color: var(--novel-primary);
  margin-bottom: var(--novel-space-2);
}

.card-title-secondary {
  color: var(--novel-secondary);
}

.card-desc {
  font-size: var(--novel-text-label);
  color: var(--novel-on-surface-variant);
  line-height: 1.6;
  margin-bottom: var(--novel-space-4);
}

.card-action {
  display: inline-flex;
  align-items: center;
  gap: var(--novel-space-2);
  color: var(--novel-primary);
  font-size: var(--novel-text-label);
  font-weight: 500;
  opacity: 0;
  transform: translateX(-8px);
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.card-action-secondary {
  color: var(--novel-secondary);
}

.entry-card:hover .card-action {
  opacity: 1;
  transform: translateX(0);
}

/* Footer ornament */
.entry-footer-ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-4);
  color: var(--novel-on-surface-variant);
  opacity: 0.5;
}

.footer-line {
  width: 80px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--novel-outline), transparent);
}

.footer-icon {
  width: 24px;
  height: 24px;
}

/* Update Log Modal - Scroll Style */
.update-log-modal {
  position: relative;
  width: 100%;
  max-width: 700px;
  max-height: 85vh;
  margin: var(--novel-space-4);
  background: var(--novel-parchment);
  border-radius: var(--novel-radius-lg);
  box-shadow: var(--novel-shadow-xl);
  overflow: hidden;
}

.scroll-rod {
  position: absolute;
  left: 0;
  right: 0;
  height: 24px;
  background: var(--novel-tertiary);
  z-index: 1;
  border-radius: var(--novel-radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.scroll-rod-top {
  top: 0;
}

.scroll-rod-bottom {
  bottom: 0;
}

.scroll-content {
  padding: calc(var(--novel-space-6) + 24px) var(--novel-space-6);
  max-height: calc(85vh - 48px);
  overflow-y: auto;
}

.scroll-content::before {
  content: '';
  position: absolute;
  inset: 24px 0;
  background: var(--novel-paper-texture);
  pointer-events: none;
  opacity: 0.5;
}

.scroll-header {
  position: relative;
  margin-bottom: var(--novel-space-6);
}

.community-section {
  position: relative;
  padding: var(--novel-space-4);
  margin-bottom: var(--novel-space-6);
  background: var(--novel-primary-container);
  border-radius: var(--novel-radius-md);
  color: var(--novel-on-primary-container);
}

.timeline-section {
  position: relative;
  padding-bottom: var(--novel-space-4);
}

.timeline-list {
  position: relative;
}

.timeline-item {
  position: relative;
  padding-left: var(--novel-space-8);
  padding-bottom: var(--novel-space-6);
}

.timeline-connector {
  position: absolute;
  left: 10px;
  top: 24px;
  bottom: 0;
  width: 2px;
  background: var(--novel-outline-variant);
}

.timeline-dot {
  position: absolute;
  left: 4px;
  top: 6px;
  width: 14px;
  height: 14px;
  background: var(--novel-primary);
  border-radius: 50%;
  box-shadow: 0 0 0 4px var(--novel-surface);
}

.timeline-content {
  position: relative;
}

.timeline-card {
  margin-top: var(--novel-space-2);
  padding: var(--novel-space-4);
  background: var(--novel-surface);
  border-radius: var(--novel-radius-md);
  border: 1px solid var(--novel-outline-variant);
}

.scroll-footer {
  position: relative;
  display: flex;
  justify-content: flex-end;
  gap: var(--novel-space-3);
  padding-top: var(--novel-space-4);
  border-top: 1px solid var(--novel-outline-variant);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all var(--novel-duration-normal) var(--novel-easing-emphasized);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .update-log-modal,
.modal-leave-to .update-log-modal {
  transform: scale(0.95) translateY(20px);
}

/* Responsive */
@media (max-width: 640px) {
  .entry-actions {
    top: var(--novel-space-2);
    right: var(--novel-space-2);
  }

  .entry-action-btn span {
    display: none;
  }

  .header-ornament {
    display: none;
  }

  .entry-title {
    font-size: var(--novel-text-headline);
  }
}
</style>
