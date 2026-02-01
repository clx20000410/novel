<!-- AIMETA P=小说工作区_小说列表管理|R=小说列表_创建|NR=不含章节编辑|E=route:/workspace#component:NovelWorkspace|X=ui|A=工作区|D=vue|S=dom,net|RD=./README.ai -->
<template>
  <div class="novel-workspace">
    <!-- Decorative background -->
    <div class="workspace-bg-decoration">
      <div class="bg-bookshelf-pattern"></div>
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
    </div>

    <!-- Snackbar notification -->
    <Teleport to="body">
      <Transition name="snackbar">
        <div v-if="deleteMessage" class="novel-snackbar" :class="deleteMessage.type">
          <svg
            v-if="deleteMessage.type === 'success'"
            class="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <svg
            v-else
            class="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{{ deleteMessage.text }}</span>
        </div>
      </Transition>
    </Teleport>

    <!-- Main content -->
    <div class="workspace-content">
      <div class="workspace-card">
        <!-- Book spine decoration -->
        <div class="card-book-spine"></div>

        <!-- Content area -->
        <div class="workspace-card-inner">
          <!-- Header -->
          <div class="workspace-header">
            <div class="header-left">
              <!-- Decorative ornament -->
              <div class="header-ornament">
                <svg class="ornament-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div>
                <h1 class="novel-headline workspace-title">我的书架</h1>
                <p class="novel-caption workspace-subtitle">收藏着您的每一个故事</p>
              </div>
              <!-- Admin link -->
              <router-link
                v-if="authStore.user?.is_admin"
                to="/admin"
                class="admin-chip"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                管理后台
              </router-link>
            </div>
            <div class="header-actions">
              <button @click="triggerBatchImport" class="novel-btn novel-btn-ghost">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                批量导入
              </button>
              <button @click="handleBatchExport" class="novel-btn novel-btn-ghost">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                批量导出
              </button>
              <button @click="goBack" class="novel-btn novel-btn-ghost">
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                返回
              </button>
            </div>
          </div>

          <!-- Divider ornament -->
          <div class="novel-divider-ornament">
            <span class="divider-line"></span>
            <svg class="divider-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
            <span class="divider-line"></span>
          </div>

          <!-- Loading State -->
          <div v-if="novelStore.isLoading" class="workspace-state">
            <div class="novel-spinner"></div>
            <p class="novel-caption mt-4">正在打开书架...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="novelStore.error" class="workspace-state">
            <div class="state-icon state-icon-error">
              <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p class="novel-body state-error-text">{{ novelStore.error }}</p>
            <button @click="loadProjects" class="novel-btn novel-btn-filled mt-4">
              重试
            </button>
          </div>

          <!-- Bookshelf Grid -->
          <div v-else class="bookshelf-grid">
            <!-- Empty State -->
            <div v-if="novelStore.projects.length === 0" class="bookshelf-empty">
              <div class="empty-icon">
                <svg class="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 class="novel-title">书架空空如也</h3>
              <p class="novel-caption">开启灵感模式，创作您的第一部作品吧！</p>
              <button @click="goToInspiration" class="novel-btn novel-btn-filled mt-6">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                开始创作
              </button>
            </div>

            <!-- Project Cards -->
            <ProjectCard
              v-for="project in novelStore.projects"
              :key="project.id"
              :project="project"
              @click="enterProject(project)"
              @detail="viewProjectDetail"
              @continue="enterProject"
              @delete="handleDeleteProject"
              @export="handleExportProject"
              @export-txt="handleExportProjectAsTxt"
            />

            <!-- Create New Project Card -->
            <div @click="goToInspiration" class="action-card action-card-create">
              <div class="action-card-inner">
                <div class="action-icon">
                  <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <span class="action-label">创建新作品</span>
              </div>
            </div>

            <!-- Import Project Card -->
            <div @click="triggerImport" class="action-card action-card-import">
              <div class="action-card-inner">
                <div v-if="isImporting" class="action-loading">
                  <div class="novel-spinner novel-spinner-sm"></div>
                  <span class="action-label">正在导入...</span>
                </div>
                <div v-else>
                  <div class="action-icon action-icon-secondary">
                    <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                  </div>
                  <span class="action-label">导入作品</span>
                </div>
              </div>
            </div>

            <!-- Hidden file inputs -->
            <input
              type="file"
              ref="fileInput"
              accept=".txt,.json"
              class="hidden"
              @change="handleFileImport"
            />
            <input
              type="file"
              ref="batchInput"
              accept=".json"
              multiple
              class="hidden"
              @change="handleBatchImport"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showDeleteDialog" class="novel-dialog-overlay" @click.self="cancelDelete">
          <div class="delete-dialog">
            <!-- Warning icon -->
            <div class="dialog-icon">
              <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>

            <h3 class="novel-title dialog-title">确认删除</h3>
            <p class="novel-body dialog-content">
              确定要删除 "<strong>{{ projectToDelete?.title }}</strong>" 吗？<br>
              <span class="novel-caption">此操作无法撤销，所有相关数据将被永久删除。</span>
            </p>

            <div class="dialog-actions">
              <button @click="cancelDelete" class="novel-btn novel-btn-ghost">
                取消
              </button>
              <button
                @click="confirmDelete"
                :disabled="isDeleting"
                class="novel-btn novel-btn-danger"
              >
                <svg v-if="isDeleting" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ isDeleting ? '删除中...' : '确认删除' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNovelStore } from '@/stores/novel'
import { useAuthStore } from '@/stores/auth'
import ProjectCard from '@/components/ProjectCard.vue'
import type { NovelProjectSummary } from '@/api/novel'
import { NovelAPI } from '@/api/novel'
import { cleanChapterText } from '@/utils/chapterText'
import { useMessage } from 'naive-ui'

const router = useRouter()
const novelStore = useNovelStore()
const authStore = useAuthStore()
const message = useMessage()

// Import related state
const fileInput = ref<HTMLInputElement | null>(null)
const isImporting = ref(false)
const isBatchImporting = ref(false)
const isBatchExporting = ref(false)
const exportingTxtProjects = ref(new Set<string>())
const batchInput = ref<HTMLInputElement | null>(null)

// Delete related state
const showDeleteDialog = ref(false)
const projectToDelete = ref<NovelProjectSummary | null>(null)
const isDeleting = ref(false)
const deleteMessage = ref<{type: 'success' | 'error', text: string} | null>(null)

const goBack = () => {
  router.push('/')
}

const goToInspiration = () => {
  router.push('/inspiration')
}

const viewProjectDetail = (projectId: string) => {
  router.push(`/detail/${projectId}`)
}

const enterProject = (project: NovelProjectSummary) => {
  if (project.status === 'concept_abandoned') {
    router.push(`/detail/${project.id}`)
    return
  }

  if (project.status === 'blueprint_ready') {
    router.push(`/novel/${project.id}`)
    return
  }

  router.push(`/inspiration?project_id=${project.id}`)
}

const loadProjects = async () => {
  await novelStore.loadProjects()
}

// Import methods
const triggerImport = () => {
  if (isImporting.value) return
  fileInput.value?.click()
}

const triggerBatchImport = () => {
  if (isBatchImporting.value) return
  batchInput.value?.click()
}

const handleFileImport = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  const lowerName = file.name.toLowerCase()
  const isTxt = lowerName.endsWith('.txt')
  const isJson = lowerName.endsWith('.json')
  if (!isTxt && !isJson) {
    alert('请上传 .txt 或 .json 格式的文件')
    return
  }

  isImporting.value = true
  try {
    if (isJson) {
      const response = await NovelAPI.importBatch(file)
      await loadProjects()
      const firstId = response.ids?.[0]
      if (firstId) {
        router.push(`/novel/${firstId}`)
      }
    } else {
      const response = await NovelAPI.importNovel(file)
      await loadProjects()
      router.push(`/novel/${response.id}`)
    }
  } catch (error: any) {
    console.error('导入失败:', error)
    alert(error.message || '导入失败，请重试')
  } finally {
    isImporting.value = false
    target.value = ''
  }
}

const handleBatchImport = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const files = Array.from(target.files)
  isBatchImporting.value = true
  try {
    let importedCount = 0
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith('.json')) {
        continue
      }
      const response = await NovelAPI.importBatch(file)
      importedCount += response.ids?.length || 0
    }
    await loadProjects()
    alert(`批量导入完成，共导入 ${importedCount} 个项目`)
  } catch (error: any) {
    console.error('批量导入失败:', error)
    alert(error.message || '批量导入失败，请重试')
  } finally {
    isBatchImporting.value = false
    target.value = ''
  }
}

const handleExportProject = async (project: NovelProjectSummary) => {
  try {
    const data = await NovelAPI.exportProject(project.id)
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const safeTitle = project.title.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 60)
    const date = new Date().toISOString().slice(0, 10)
    const filename = `novel_project_${safeTitle || project.id}_${date}.json`
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  } catch (error: any) {
    console.error('导出失败:', error)
    alert(error.message || '导出失败，请重试')
  }
}

const sanitizeFileName = (name: string): string => {
  return name.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 60)
}

const buildChapterHeading = (chapterNumber: number, title: string | null | undefined): string => {
  const numberLabel = `第${chapterNumber}章`
  const trimmedTitle = title?.trim() || ''
  if (!trimmedTitle) return numberLabel
  return trimmedTitle.startsWith(numberLabel) ? trimmedTitle : `${numberLabel} ${trimmedTitle}`
}

const pickExportedChapterText = (chapter: any): string => {
  const versions = Array.isArray(chapter?.versions) ? chapter.versions : []
  if (versions.length === 0) return ''

  const selectedIndex = Number.isInteger(chapter?.selected_version_index)
    ? (chapter.selected_version_index as number)
    : versions.length - 1

  const raw = versions[selectedIndex]?.content ?? versions[versions.length - 1]?.content ?? ''
  return cleanChapterText(String(raw ?? ''))
}

const handleExportProjectAsTxt = async (project: NovelProjectSummary) => {
  if (exportingTxtProjects.value.has(project.id)) return
  exportingTxtProjects.value.add(project.id)

  try {
    const data = await NovelAPI.exportProject(project.id)
    const projectTitle = String(data?.project?.title ?? project.title ?? project.id)
    const chapters = Array.isArray(data?.chapters) ? data.chapters : []

    const blocks: string[] = []
    blocks.push(projectTitle)
    blocks.push('')

    for (const chapter of chapters.slice().sort((a: any, b: any) => (a?.chapter_number ?? 0) - (b?.chapter_number ?? 0))) {
      const chapterNumber = Number(chapter?.chapter_number ?? 0)
      if (!chapterNumber) continue

      const content = pickExportedChapterText(chapter)
      if (!content.trim()) continue

      const heading = buildChapterHeading(chapterNumber, chapter?.title)
      blocks.push(heading)
      blocks.push('')
      blocks.push(content.trimEnd())
      blocks.push('')
      blocks.push('')
    }

    if (blocks.length <= 2) {
      message.warning('没有可导出的正文内容')
      return
    }

    const blob = new Blob([blocks.join('\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const safeTitle = sanitizeFileName(projectTitle) || project.id
    const date = new Date().toISOString().slice(0, 10)
    const filename = `novel_${safeTitle}_${date}.txt`
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
    message.success('TXT 已导出')
  } catch (error: any) {
    console.error('导出TXT失败:', error)
    message.error(error.message || '导出TXT失败，请重试')
  } finally {
    exportingTxtProjects.value.delete(project.id)
  }
}

const handleBatchExport = async () => {
  if (isBatchExporting.value) return
  isBatchExporting.value = true
  try {
    const data = await NovelAPI.exportBatch()
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const date = new Date().toISOString().slice(0, 10)
    const filename = `novel_projects_bundle_${date}.json`
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  } catch (error: any) {
    console.error('批量导出失败:', error)
    alert(error.message || '批量导出失败，请重试')
  } finally {
    isBatchExporting.value = false
  }
}

// Delete methods
const handleDeleteProject = (projectId: string) => {
  const project = novelStore.projects.find(p => p.id === projectId)
  if (project) {
    projectToDelete.value = project
    showDeleteDialog.value = true
  }
}

const cancelDelete = () => {
  showDeleteDialog.value = false
  projectToDelete.value = null
}

const confirmDelete = async () => {
  if (!projectToDelete.value) return

  isDeleting.value = true
  try {
    await novelStore.deleteProjects([projectToDelete.value.id])
    deleteMessage.value = { type: 'success', text: `作品 "${projectToDelete.value.title}" 已从书架移除` }
    showDeleteDialog.value = false
    projectToDelete.value = null

    setTimeout(() => {
      deleteMessage.value = null
    }, 3000)
  } catch (error) {
    console.error('删除项目失败:', error)
    deleteMessage.value = { type: 'error', text: '删除失败，请重试' }

    setTimeout(() => {
      deleteMessage.value = null
    }, 3000)
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.novel-workspace {
  min-height: 100vh;
  padding: var(--novel-space-6);
  padding-bottom: var(--novel-space-16);
  background: var(--novel-surface-dim);
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
}

/* Background decorations */
.workspace-bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-bookshelf-pattern {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: linear-gradient(180deg, transparent 0%, var(--novel-surface-container) 100%);
  opacity: 0.6;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.4;
}

.bg-circle-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, var(--novel-primary-container) 0%, transparent 70%);
  top: -150px;
  right: -100px;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, var(--novel-secondary-container) 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
}

/* Main content */
.workspace-content {
  position: relative;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  animation: content-appear 0.6s var(--novel-easing-emphasized);
}

@keyframes content-appear {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Workspace card */
.workspace-card {
  position: relative;
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  box-shadow: var(--novel-shadow-lg);
  overflow: hidden;
}

.card-book-spine {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 20px;
  background: var(--novel-book-spine);
  box-shadow: inset -4px 0 8px rgba(0, 0, 0, 0.15);
}

.workspace-card-inner {
  padding: var(--novel-space-8);
  padding-left: calc(var(--novel-space-8) + 20px);
  position: relative;
}

.workspace-card-inner::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  pointer-events: none;
  opacity: 0.3;
}

/* Header */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--novel-space-4);
  margin-bottom: var(--novel-space-6);
  position: relative;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--novel-space-4);
}

.header-ornament {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--novel-primary-container);
  border-radius: var(--novel-radius-lg);
  color: var(--novel-on-primary-container);
}

.ornament-icon {
  width: 28px;
  height: 28px;
}

.workspace-title {
  color: var(--novel-on-surface);
  margin: 0;
}

.workspace-subtitle {
  color: var(--novel-on-surface-variant);
  margin: 0;
}

.admin-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-2) var(--novel-space-3);
  background: var(--novel-tertiary-container);
  color: var(--novel-on-tertiary-container);
  border-radius: var(--novel-radius-full);
  font-size: var(--novel-text-caption);
  font-weight: 500;
  text-decoration: none;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.admin-chip:hover {
  background: var(--novel-tertiary);
  color: var(--novel-on-tertiary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
}

/* Divider ornament */
.novel-divider-ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-4);
  margin-bottom: var(--novel-space-6);
  position: relative;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--novel-outline-variant), transparent);
}

.divider-icon {
  width: 20px;
  height: 20px;
  color: var(--novel-primary);
}

/* States */
.workspace-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--novel-space-16) 0;
  position: relative;
}

.state-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--novel-space-4);
}

.state-icon-error {
  background: var(--novel-error-container);
  color: var(--novel-error);
}

.state-error-text {
  color: var(--novel-error);
}

/* Bookshelf grid */
.bookshelf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--novel-space-6);
  position: relative;
}

/* Empty state */
.bookshelf-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--novel-space-16) 0;
  text-align: center;
}

.empty-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
  margin-bottom: var(--novel-space-6);
}

/* Action cards */
.action-card {
  position: relative;
  min-height: 200px;
  background: var(--novel-surface);
  border: 2px dashed var(--novel-outline-variant);
  border-radius: var(--novel-radius-lg);
  cursor: pointer;
  transition: all var(--novel-duration-normal) var(--novel-easing-emphasized);
  overflow: hidden;
}

.action-card:hover {
  border-color: var(--novel-primary);
  transform: translateY(-4px);
  box-shadow: var(--novel-shadow-md);
}

.action-card-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  padding: var(--novel-space-6);
  text-align: center;
}

.action-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
  margin-bottom: var(--novel-space-4);
  transition: transform var(--novel-duration-normal) var(--novel-easing-bounce);
}

.action-card:hover .action-icon {
  transform: scale(1.1);
}

.action-icon-secondary {
  background: var(--novel-secondary-container);
  color: var(--novel-on-secondary-container);
}

.action-label {
  font-size: var(--novel-text-label);
  font-weight: 500;
  color: var(--novel-on-surface-variant);
}

.action-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--novel-space-3);
}

/* Delete dialog */
.delete-dialog {
  width: 100%;
  max-width: 420px;
  margin: var(--novel-space-4);
  padding: var(--novel-space-6);
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  box-shadow: var(--novel-shadow-xl);
  text-align: center;
}

.dialog-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--novel-space-4);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--novel-error-container);
  color: var(--novel-error);
}

.dialog-title {
  color: var(--novel-on-surface);
  margin-bottom: var(--novel-space-3);
}

.dialog-content {
  color: var(--novel-on-surface-variant);
  margin-bottom: var(--novel-space-6);
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  justify-content: center;
  gap: var(--novel-space-3);
}

/* Snackbar */
.novel-snackbar {
  position: fixed;
  bottom: var(--novel-space-6);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: var(--novel-space-3);
  padding: var(--novel-space-4) var(--novel-space-6);
  background: var(--novel-surface-container-high);
  border-radius: var(--novel-radius-lg);
  box-shadow: var(--novel-shadow-lg);
  z-index: 1000;
}

.novel-snackbar.success {
  border-left: 4px solid var(--novel-success);
}

.novel-snackbar.success svg {
  color: var(--novel-success);
}

.novel-snackbar.error {
  border-left: 4px solid var(--novel-error);
}

.novel-snackbar.error svg {
  color: var(--novel-error);
}

/* Snackbar transitions */
.snackbar-enter-active,
.snackbar-leave-active {
  transition: all var(--novel-duration-normal) var(--novel-easing-emphasized);
}

.snackbar-enter-from,
.snackbar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
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

.modal-enter-from .delete-dialog,
.modal-leave-to .delete-dialog {
  transform: scale(0.95) translateY(20px);
}

/* Danger button */
.novel-btn-danger {
  background: var(--novel-error);
  color: var(--novel-on-error);
}

.novel-btn-danger:hover:not(:disabled) {
  background: var(--novel-error-dark, #b91c1c);
}

/* Responsive */
@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    gap: var(--novel-space-4);
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .header-left {
    flex-wrap: wrap;
  }

  .workspace-card-inner {
    padding: var(--novel-space-4);
    padding-left: calc(var(--novel-space-4) + 16px);
  }

  .card-book-spine {
    width: 16px;
  }

  .bookshelf-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .novel-workspace {
    padding: var(--novel-space-4);
  }

  .header-ornament {
    display: none;
  }

  .admin-chip {
    padding: var(--novel-space-1) var(--novel-space-2);
    font-size: 11px;
  }
}
</style>
