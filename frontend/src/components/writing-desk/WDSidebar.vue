<!-- AIMETA P=写作台侧边栏_章节目录|R=章节列表_导航|NR=不含内容编辑|E=component:WDSidebar|X=ui|A=侧边栏|D=vue|S=dom|RD=./README.ai -->
<template>
  <div>
    <!-- 侧边栏遮罩 (移动端) -->
    <div
      v-if="sidebarOpen"
      @click="$emit('closeSidebar')"
      class="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
    ></div>

    <!-- 左侧：蓝图和章节列表 -->
    <div
      :class="[
        'md-card md-card-elevated transition-all duration-300 h-full',
        'lg:relative lg:translate-x-0 lg:w-80 lg:flex-shrink-0',
        sidebarOpen
          ? 'fixed left-4 top-20 bottom-4 w-80 z-50 translate-x-0'
          : 'lg:w-80 lg:flex-shrink-0 -translate-x-full absolute lg:relative'
      ]"
      style="border-radius: var(--md-radius-xl);"
    >
      <div class="h-full flex flex-col">
        <!-- 蓝图预览卡片 -->
        <div class="md-card-header flex-shrink-0">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full flex items-center justify-center" style="background-color: var(--md-primary-container);">
              <svg class="w-5 h-5" style="color: var(--md-on-primary-container);" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <div>
              <h2 class="md-title-medium font-semibold">故事蓝图</h2>
              <p class="md-body-small md-on-surface-variant">{{ project.blueprint?.style || '未设定风格' }}</p>
            </div>
          </div>

          <div class="space-y-3">
            <div class="md-card md-card-filled p-3" style="border-radius: var(--md-radius-md);">
              <h3 class="md-label-large font-semibold" style="color: var(--md-on-primary-container);">故事概要</h3>
              <Tooltip :text="project.blueprint?.one_sentence_summary">
                <p class="md-body-small line-clamp-3" style="color: var(--md-on-surface-variant);">{{ project.blueprint?.one_sentence_summary || '暂无概要' }}</p>
              </Tooltip>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div class="md-card md-card-outlined p-2 text-center" style="border-radius: var(--md-radius-md);">
                <div class="md-title-small font-semibold" style="color: var(--md-primary);">{{ characterCount }}</div>
                <div class="md-label-small md-on-surface-variant">角色</div>
              </div>
              <div class="md-card md-card-outlined p-2 text-center" style="border-radius: var(--md-radius-md);">
                <div class="md-title-small font-semibold" style="color: var(--md-secondary);">{{ relationshipCount }}</div>
                <div class="md-label-small md-on-surface-variant">关系</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 章节列表 -->
        <div ref="listContainer" class="flex-1 overflow-y-auto">
          <!-- 吸顶的标题和 Tab 切换 -->
          <div class="sticky top-0 z-10 p-6 pb-4 bg-[var(--md-surface)] backdrop-blur-sm">
            <div class="flex items-center justify-between mb-4">
              <h3 class="md-title-medium font-semibold">章节大纲</h3>
              <span class="md-chip md-chip-filter selected">
                {{ totalChapters }} 章
              </span>
            </div>
            <!-- Tab 切换 -->
            <div class="flex gap-1 p-1 rounded-xl" style="background-color: var(--md-surface-container);">
              <button
                @click="activeTab = 'incomplete'"
                :class="[
                  'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200',
                  activeTab === 'incomplete'
                    ? 'bg-[var(--md-primary)] text-[var(--md-on-primary)] shadow-sm'
                    : 'text-[var(--md-on-surface-variant)] hover:bg-[var(--md-surface-container-high)]'
                ]"
              >
                未完成 ({{ incompleteChapters.length }})
              </button>
              <button
                @click="activeTab = 'completed'"
                :class="[
                  'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200',
                  activeTab === 'completed'
                    ? 'bg-[var(--md-primary)] text-[var(--md-on-primary)] shadow-sm'
                    : 'text-[var(--md-on-surface-variant)] hover:bg-[var(--md-surface-container-high)]'
                ]"
              >
                已完成 ({{ completedChapters.length }})
              </button>
            </div>
          </div>

          <div class="px-6 pb-6">
            <div v-if="project.blueprint?.chapter_outline?.length">
              <!-- 当前 Tab 对应的章节列表 -->
              <div v-if="currentTabChapters.length" class="space-y-3">
                <div
                  v-for="(chapter, index) in currentTabChapters"
                  :key="chapter.chapter_number"
                  :ref="el => setChapterRef(chapter.chapter_number, el)"
                  @click="$emit('selectChapter', chapter.chapter_number)"
                  :class="[
                    'group relative cursor-pointer p-4 pr-12 m3-chapter-card m3-stagger',
                    selectedForDeletion.includes(chapter.chapter_number)
                      ? 'm3-chapter-danger'
                      : selectedChapterNumber === chapter.chapter_number
                      ? 'm3-chapter-selected md-elevation-1'
                      : 'hover:md-elevation-1'
                  ]"
                  :style="{ animationDelay: `${index * 40}ms` }"
                >
                  <div class="flex items-start gap-3">
                    <div class="flex-shrink-0 pt-1">
                      <input
                        v-if="!isChapterCompleted(chapter.chapter_number)"
                        type="checkbox"
                        :disabled="isChapterCompleted(chapter.chapter_number)"
                        :checked="selectedForDeletion.includes(chapter.chapter_number)"
                        @click.stop="toggleSelection(chapter.chapter_number)"
                        class="h-4 w-4 rounded border-[var(--md-outline)] text-[var(--md-primary)] focus:ring-[var(--md-primary)] disabled:opacity-50 accent-[var(--md-primary)]"
                      />
                    </div>
                    <div
                      :class="[
                        'w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0',
                        isChapterCompleted(chapter.chapter_number)
                          ? 'bg-[var(--md-success)] text-[var(--md-on-success)]'
                          : isChapterGenerating(chapter.chapter_number) || isChapterEvaluating(chapter.chapter_number) || isChapterSelecting(chapter.chapter_number)
                          ? 'bg-[var(--md-primary)] text-[var(--md-on-primary)] animate-pulse'
                          : isChapterFailed(chapter.chapter_number)
                          ? 'bg-[var(--md-error)] text-[var(--md-on-error)]'
                          : selectedChapterNumber === chapter.chapter_number
                          ? 'bg-[var(--md-primary)] text-[var(--md-on-primary)]'
                          : 'bg-[var(--md-surface-container-highest)] text-[var(--md-on-surface-variant)]'
                      ]"
                    >
                      <svg v-if="isChapterCompleted(chapter.chapter_number)" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                      </svg>
                      <svg v-else-if="isChapterGenerating(chapter.chapter_number) || isChapterSelecting(chapter.chapter_number)" class="w-4 h-4 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                      </svg>
                      <svg v-else-if="isChapterEvaluating(chapter.chapter_number)" class="w-4 h-4 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 2a6 6 0 00-6 6v3.586l-1.707 1.707A1 1 0 003 15v1a1 1 0 001 1h12a1 1 0 001-1v-1a1 1 0 00-.293-.707L16 11.586V8a6 6 0 00-6-6zM8.05 17a2 2 0 103.9 0H8.05z"></path>
                      </svg>
                      <svg v-else-if="isChapterFailed(chapter.chapter_number)" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                      </svg>
                      <span v-else>{{ chapter.chapter_number }}</span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <Tooltip fullWidth :text="getChapterTooltipText(chapter)">
                        <div class="space-y-1">
                          <div class="md-label-small md-on-surface-variant">
                            {{ getChapterNumberLabel(chapter.chapter_number) }}
                          </div>
                          <h4 class="md-body-medium font-semibold whitespace-normal break-words leading-snug">
                            {{ getChapterTitle(chapter) }}
                          </h4>
                        </div>
                      </Tooltip>
                    </div>

                    <!-- 章节操作按钮 -->
                    <div
                      class="absolute right-2 top-2 flex items-center gap-1 opacity-100 transition-opacity duration-200 lg:opacity-0 lg:group-hover:opacity-100"
                    >
                      <button
                        v-if="!isChapterCompleted(chapter.chapter_number)"
                        @click.stop="$emit('editChapter', chapter)"
                        class="md-icon-btn md-ripple"
                        title="编辑大纲"
                      >
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z"></path>
                          <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd"></path>
                        </svg>
                      </button>
                      <button
                        v-if="canGenerateChapter(chapter.chapter_number) || isChapterFailed(chapter.chapter_number) || hasChapterInProgress(chapter.chapter_number)"
                        @click.stop="confirmGenerateChapter(chapter.chapter_number)"
                        :disabled="generatingChapter === chapter.chapter_number || isChapterGenerating(chapter.chapter_number)"
                        class="md-icon-btn md-ripple disabled:opacity-50"
                        style="color: var(--md-primary);"
                        :title="isChapterCompleted(chapter.chapter_number) ? '重新生成' : isChapterFailed(chapter.chapter_number) ? '重试' : hasChapterInProgress(chapter.chapter_number) ? '重新生成版本' : '开始创作'"
                      >
                        <svg v-if="generatingChapter === chapter.chapter_number || isChapterGenerating(chapter.chapter_number)" class="w-4 h-4 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                        </svg>
                        <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"></path>
                        </svg>
                      </button>
                      <!-- Batch delete replaces the single delete button -->
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="md-body-small md-on-surface-variant text-center py-8">
                <svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                {{ activeTab === 'completed' ? '暂无已完成章节' : '暂无未完成章节' }}
              </div>
            </div>
          <div v-else class="text-center py-8 md-body-medium md-on-surface-variant">
              <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9z"></path>
              </svg>
              <p>暂无章节大纲</p>
            </div>
            <div v-if="selectedForDeletion.length > 0" class="mt-4">
              <button
                @click="handleDeleteSelected"
                class="md-btn md-btn-filled md-ripple w-full flex items-center justify-center gap-2"
                style="background-color: var(--md-error); color: var(--md-on-error);"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clip-rule="evenodd"></path>
                </svg>
                <span>删除选中的 {{ selectedForDeletion.length }} 章</span>
              </button>
            </div>
            <!-- 批量生成按钮和进度显示 -->
            <div v-if="props.project.blueprint?.chapter_outline?.length" class="mt-4">
              <div v-if="props.isBatchGenerating && props.batchGeneratingProgress" class="md-card md-card-filled p-4" style="background-color: var(--md-primary-container); border-radius: var(--md-radius-md);">
                <div class="flex items-center gap-3 mb-2">
                  <div class="md-spinner w-5 h-5" style="border-color: var(--md-on-primary-container); border-top-color: transparent;"></div>
                  <span class="md-body-medium font-medium" style="color: var(--md-on-primary-container);">
                    正在生成 {{ props.batchGeneratingProgress.current }} / {{ props.batchGeneratingProgress.total }} 章
                  </span>
                </div>
                <div class="w-full h-2 rounded-full overflow-hidden" style="background-color: var(--md-surface-container-highest);">
                  <div
                    class="h-full rounded-full transition-all duration-300"
                    style="background-color: var(--md-primary);"
                    :style="{ width: `${(props.batchGeneratingProgress.current / props.batchGeneratingProgress.total) * 100}%` }"
                  ></div>
                </div>
                <button
                  @click="$emit('stopBatchGenerate')"
                  class="md-btn md-btn-text md-ripple w-full mt-3 flex items-center justify-center gap-2"
                  style="color: var(--md-error);"
                >
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd" />
                  </svg>
                  停止生成
                </button>
              </div>
              <button
                v-else
                @click="$emit('batchGenerate')"
                :disabled="props.isGeneratingOutline || props.generatingChapter !== null"
                class="md-btn md-btn-filled md-ripple w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                style="background-color: var(--md-primary); color: var(--md-on-primary);"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                批量生成章节
              </button>
            </div>
            <div class="mt-4">
              <button
                @click="$emit('generateOutline')"
                :disabled="props.isGeneratingOutline"
                class="md-btn md-btn-tonal md-ripple w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg v-if="props.isGeneratingOutline" class="w-5 h-5 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                </svg>
                <svg v-else class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"></path>
                </svg>
                <span>{{ props.isGeneratingOutline ? '生成中...' : '生成后续大纲' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import { globalAlert } from '@/composables/useAlert'
import type { ChapterOutline, NovelProject } from '@/api/novel'
import Tooltip from '@/components/Tooltip.vue'

interface Props {
  project: NovelProject
  sidebarOpen: boolean
  selectedChapterNumber: number | null
  generatingChapter: number | null
  evaluatingChapter: number | null
  isGeneratingOutline: boolean
  isBatchGenerating: boolean
  batchGeneratingProgress: { current: number; total: number } | null
}

const props = defineProps<Props>()

const emit = defineEmits(['closeSidebar', 'selectChapter', 'generateChapter', 'editChapter', 'deleteChapter', 'generateOutline', 'batchGenerate', 'stopBatchGenerate'])

const selectedForDeletion = ref<number[]>([])
const listContainer = ref<HTMLElement | null>(null)
const chapterRefs = ref<Record<number, HTMLElement | null>>({})
const activeTab = ref<'completed' | 'incomplete'>('incomplete')

const characterCount = computed(() => {
  return props.project?.blueprint?.characters?.length || 0
})

const relationshipCount = computed(() => {
  return props.project?.blueprint?.relationships?.length || 0
})

const lastChapterNumber = computed(() => {
  if (!props.project?.blueprint?.chapter_outline || props.project.blueprint.chapter_outline.length === 0) {
    return null
  }
  return Math.max(...props.project.blueprint.chapter_outline.map(ch => ch.chapter_number))
})

const totalChapters = computed(() => {
  return props.project?.blueprint?.chapter_outline?.length || 0
})

const completedChapters = computed(() => {
  if (!props.project?.blueprint?.chapter_outline) return []
  return props.project.blueprint.chapter_outline
    .filter(ch => isChapterCompleted(ch.chapter_number))
    .sort((a, b) => b.chapter_number - a.chapter_number) // 倒序：最新章节在前
})

const incompleteChapters = computed(() => {
  if (!props.project?.blueprint?.chapter_outline) return []
  return props.project.blueprint.chapter_outline.filter(ch => !isChapterCompleted(ch.chapter_number))
})

const currentTabChapters = computed(() => {
  return activeTab.value === 'completed' ? completedChapters.value : incompleteChapters.value
})

const getChapterNumberLabel = (chapterNumber: number) => {
  return `第${chapterNumber}章`
}

const getChapterTitle = (chapter: ChapterOutline) => {
  return chapter.title?.trim() || '无标题'
}

const getChapterTooltipText = (chapter: ChapterOutline) => {
  return `${getChapterNumberLabel(chapter.chapter_number)} ${getChapterTitle(chapter)}`
}

function toggleSelection(chapterNumber: number) {
  if (isChapterCompleted(chapterNumber)) return
  const index = selectedForDeletion.value.indexOf(chapterNumber)
  if (index > -1) {
    selectedForDeletion.value.splice(index, 1)
  } else {
    selectedForDeletion.value.push(chapterNumber)
  }
}

function handleDeleteSelected() {
  if (selectedForDeletion.value.length === 0) return

  const sortedSelection = [...selectedForDeletion.value].sort((a, b) => a - b)

  if (!lastChapterNumber.value || !sortedSelection.includes(lastChapterNumber.value)) {
    alert('批量删除必须包含最后一章。')
    return
  }

  const isContinuous = sortedSelection.every((num, i) => {
    return i === 0 || num === sortedSelection[i - 1] + 1
  })
  if (!isContinuous) {
    alert('只能删除连续的章节块。')
    return
  }

  emit('deleteChapter', sortedSelection)
  selectedForDeletion.value = []
}

async function confirmGenerateChapter(chapterNumber: number) {
  const confirmed = await globalAlert.showConfirm('重新生成会覆盖当前章节的生成结果，确定继续吗？', '重新生成确认')
  if (confirmed) {
    emit('generateChapter', chapterNumber)
  }
}

function setChapterRef(chapterNumber: number, el: Element | ComponentPublicInstance | null) {
  if (!el) {
    delete chapterRefs.value[chapterNumber]
    return
  }

  const element = el instanceof Element ? el : (el.$el instanceof Element ? el.$el : null)

  if (element) {
    chapterRefs.value[chapterNumber] = element as HTMLElement
  }
}

// 章节状态检查
const isChapterCompleted = (chapterNumber: number) => {
  if (!props.project?.chapters) return false
  const chapter = props.project.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'successful'
}

const hasChapterInProgress = (chapterNumber: number) => {
  if (!props.project?.chapters) return false
  const chapter = props.project.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'waiting_for_confirm'
}

const isChapterGenerating = (chapterNumber: number) => {
  if (!props.project?.chapters) return false
  const chapter = props.project.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'generating'
}

const isChapterEvaluating = (chapterNumber: number) => {
  if (!props.project?.chapters) return false
  const chapter = props.project.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'evaluating'
}

const isChapterFailed = (chapterNumber: number) => {
  if (!props.project?.chapters) return false
  const chapter = props.project.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'failed'
}

const isChapterSelecting = (chapterNumber: number) => {
  if (!props.project?.chapters) return false
  const chapter = props.project.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'selecting'
}

const canGenerateChapter = (chapterNumber: number) => {
  if (!props.project?.blueprint?.chapter_outline) return false

  const outlines = props.project.blueprint.chapter_outline.sort((a, b) => a.chapter_number - b.chapter_number)
  
  for (const outline of outlines) {
    if (outline.chapter_number >= chapterNumber) break
    
    const chapter = props.project?.chapters.find(ch => ch.chapter_number === outline.chapter_number)
    if (!chapter || chapter.generation_status !== 'successful') {
      return false
    }
  }

  const currentChapter = props.project?.chapters.find(ch => ch.chapter_number === chapterNumber)
  if (currentChapter && currentChapter.generation_status === 'successful') {
    return true
  }

  return true
}
</script>

<style scoped>
.m3-chapter-card {
  border-radius: var(--md-radius-lg);
  border: 1px solid var(--md-outline-variant);
  background-color: var(--md-surface);
  transition: all var(--md-duration-medium) var(--md-easing-standard);
}

.m3-chapter-card:hover {
  background-color: var(--md-surface-container-low);
}

.m3-chapter-selected {
  border-color: var(--md-primary);
  background-color: var(--md-primary-container);
}

.m3-chapter-danger {
  border-color: var(--md-error);
  background-color: var(--md-error-container);
}

.m3-stagger {
  animation: m3-rise 0.45s ease-out both;
}

@keyframes m3-rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
