<!-- AIMETA P=写作台_章节编辑主页面|R=写作界面_章节管理|NR=不含详情展示|E=route:/novel/:id#component:WritingDesk|X=ui|A=写作台|D=vue|S=dom,net|RD=./README.ai -->
<template>
  <div class="writing-desk">
    <!-- Decorative background -->
    <div class="desk-bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-paper-texture"></div>
    </div>

    <WDHeader
      :project="project"
      :progress="progress"
      :completed-chapters="completedChapters"
      :total-chapters="totalChapters"
      :is-refreshing="isRefreshing"
      :auto-mode="autoMode"
      @go-back="goBack"
      @view-project-detail="viewProjectDetail"
      @toggle-sidebar="toggleSidebar"
      @refresh="refreshProject"
      @toggle-auto-mode="toggleAutoMode"
    />

    <!-- 主要内容区域 -->
    <div class="desk-content">
      <!-- 加载状态 -->
      <div v-if="novelStore.isLoading" class="loading-state">
        <div class="loading-card">
          <div class="loading-spinner">
            <svg class="spinner-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <p class="loading-text">正在加载项目数据...</p>
        </div>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="novelStore.error" class="error-state">
        <div class="error-card">
          <div class="error-icon-wrapper">
            <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <h3 class="error-title">加载失败</h3>
          <p class="error-message">{{ novelStore.error }}</p>
          <button @click="loadProject" class="novel-btn novel-btn-tonal">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            重新加载
          </button>
        </div>
      </div>

      <!-- 主要内容 -->
      <div v-else-if="project" class="desk-main">
        <WDSidebar
          :project="project"
          :sidebar-open="sidebarOpen"
          :selected-chapter-number="selectedChapterNumber"
          :generating-chapter="generatingChapter"
          :evaluating-chapter="evaluatingChapter"
          :is-generating-outline="isGeneratingOutline"
          :is-batch-generating="isBatchGenerating"
          :batch-generating-progress="batchGeneratingProgress"
          @close-sidebar="closeSidebar"
          @select-chapter="selectChapter"
          @generate-chapter="generateChapter"
          @edit-chapter="openEditChapterModal"
          @delete-chapter="deleteChapter"
          @generate-outline="generateOutline"
          @batch-generate="showBatchGenerateModalHandler"
          @stop-batch-generate="stopBatchGenerate"
        />

        <div class="desk-workspace">
          <WDWorkspace
            :project="project"
            :selected-chapter-number="selectedChapterNumber"
            :generating-chapter="generatingChapter"
            :evaluating-chapter="evaluatingChapter"
            :show-version-selector="showVersionSelector"
            :chapter-generation-result="chapterGenerationResult"
            :selected-version-index="selectedVersionIndex"
            :available-versions="availableVersions"
            :is-selecting-version="isSelectingVersion"
            @regenerate-chapter="regenerateChapter"
            @evaluate-chapter="evaluateChapter"
            @hide-version-selector="hideVersionSelector"
            @update:selected-version-index="selectedVersionIndex = $event"
            @show-version-detail="showVersionDetail"
            @confirm-version-selection="confirmVersionSelection"
            @generate-chapter="generateChapter"
            @show-evaluation-detail="showEvaluationDetailModal = true"
            @fetch-chapter-status="fetchChapterStatus"
            @edit-chapter="editChapterContent"
          />
        </div>
      </div>
    </div>

    <WDVersionDetailModal
      :show="showVersionDetailModal"
      :detail-version-index="detailVersionIndex"
      :version="availableVersions[detailVersionIndex]"
      :is-current="isCurrentVersion(detailVersionIndex)"
      @close="closeVersionDetail"
      @select-version="selectVersionFromDetail"
    />
    <WDEvaluationDetailModal
      :show="showEvaluationDetailModal"
      :evaluation="selectedChapter?.evaluation || null"
      @close="showEvaluationDetailModal = false"
    />
    <WDEditChapterModal
      :show="showEditChapterModal"
      :chapter="editingChapter"
      @close="showEditChapterModal = false"
      @save="saveChapterChanges"
    />
    <WDGenerateOutlineModal
      :show="showGenerateOutlineModal"
      @close="showGenerateOutlineModal = false"
      @generate="handleGenerateOutline"
    />
    <WDBatchGenerateModal
      :show="showBatchGenerateModal"
      :chapters="project?.blueprint?.chapter_outline || []"
      @close="showBatchGenerateModal = false"
      @generate="batchGenerateChapters"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNovelStore } from '@/stores/novel'
import type { Chapter, ChapterOutline, ChapterGenerationResponse, ChapterVersion } from '@/api/novel'
import { globalAlert } from '@/composables/useAlert'
import WDHeader from '@/components/writing-desk/WDHeader.vue'
import WDSidebar from '@/components/writing-desk/WDSidebar.vue'
import WDWorkspace from '@/components/writing-desk/WDWorkspace.vue'
import WDVersionDetailModal from '@/components/writing-desk/WDVersionDetailModal.vue'
import WDEvaluationDetailModal from '@/components/writing-desk/WDEvaluationDetailModal.vue'
import WDEditChapterModal from '@/components/writing-desk/WDEditChapterModal.vue'
import WDGenerateOutlineModal from '@/components/writing-desk/WDGenerateOutlineModal.vue'
import WDBatchGenerateModal from '@/components/writing-desk/WDBatchGenerateModal.vue'

interface Props {
  id: string
}

const props = defineProps<Props>()
const router = useRouter()
const novelStore = useNovelStore()

// 状态管理
const selectedChapterNumber = ref<number | null>(null)
const chapterGenerationResult = ref<ChapterGenerationResponse | null>(null)
const selectedVersionIndex = ref<number>(0)
const generatingChapter = ref<number | null>(null)
const sidebarOpen = ref(false)
const showVersionDetailModal = ref(false)
const detailVersionIndex = ref<number>(0)
const showEvaluationDetailModal = ref(false)
const showEditChapterModal = ref(false)
const editingChapter = ref<ChapterOutline | null>(null)
const isGeneratingOutline = ref(false)
const showGenerateOutlineModal = ref(false)
const isRefreshing = ref(false)

// 批量生成相关状态
const isBatchGenerating = ref(false)
const batchGeneratingProgress = ref<{ current: number; total: number } | null>(null)
const batchGeneratingAbortController = ref<AbortController | null>(null)
const showBatchGenerateModal = ref(false)

// 自动模式状态：开启后生成完成会自动选择最佳版本并继续下一章
const autoMode = ref(false)

// 切换自动模式
const toggleAutoMode = () => {
  autoMode.value = !autoMode.value
  if (autoMode.value) {
    globalAlert.showSuccess('自动模式已开启：生成完成后将自动选择 AI 推荐的最佳版本并继续下一章', '模式切换')
  } else {
    globalAlert.showSuccess('手动模式已开启：需要手动选择版本', '模式切换')
  }
}

// 计算属性
const project = computed(() => novelStore.currentProject)

const selectedChapter = computed(() => {
  if (!project.value || selectedChapterNumber.value === null) return null
  return project.value.chapters.find(ch => ch.chapter_number === selectedChapterNumber.value) || null
})

const showVersionSelector = computed(() => {
  if (!selectedChapter.value) return false
  const status = selectedChapter.value.generation_status
  return status === 'waiting_for_confirm' || status === 'evaluating' || status === 'evaluation_failed' || status === 'selecting'
})

const evaluatingChapter = computed(() => {
  if (selectedChapter.value?.generation_status === 'evaluating') {
    return selectedChapter.value.chapter_number
  }
  return null
})

const isSelectingVersion = computed(() => {
  return selectedChapter.value?.generation_status === 'selecting'
})

const selectedChapterOutline = computed(() => {
  if (!project.value?.blueprint?.chapter_outline || selectedChapterNumber.value === null) return null
  return project.value.blueprint.chapter_outline.find(ch => ch.chapter_number === selectedChapterNumber.value) || null
})

const progress = computed(() => {
  if (!project.value?.blueprint?.chapter_outline) return 0
  const totalChapters = project.value.blueprint.chapter_outline.length
  const completedChapters = project.value.chapters.filter(ch => ch.content).length
  return Math.round((completedChapters / totalChapters) * 100)
})

const totalChapters = computed(() => {
  return project.value?.blueprint?.chapter_outline?.length || 0
})

const completedChapters = computed(() => {
  return project.value?.chapters?.filter(ch => ch.content)?.length || 0
})

const isCurrentVersion = (versionIndex: number) => {
  if (!selectedChapter.value?.content || !availableVersions.value?.[versionIndex]?.content) return false

  // 使用cleanVersionContent函数清理内容进行比较
  const cleanCurrentContent = cleanVersionContent(selectedChapter.value.content)
  const cleanVersionContentStr = cleanVersionContent(availableVersions.value[versionIndex].content)

  return cleanCurrentContent === cleanVersionContentStr
}

const cleanVersionContent = (content: string): string => {
  if (!content) return ''

  // 尝试解析JSON，看是否是完整的章节对象
  try {
    const parsed = JSON.parse(content)
    const extractContent = (value: any): string | null => {
      if (!value) return null
      if (typeof value === 'string') return value
      if (Array.isArray(value)) {
        for (const item of value) {
          const nested = extractContent(item)
          if (nested) return nested
        }
        return null
      }
      if (typeof value === 'object') {
        for (const key of ['content', 'chapter_content', 'chapter_text', 'text', 'body', 'story']) {
          if (value[key]) {
            const nested = extractContent(value[key])
            if (nested) return nested
          }
        }
      }
      return null
    }
    const extracted = extractContent(parsed)
    if (extracted) {
      // 如果是章节对象/数组，提取正文
      content = extracted
    }
  } catch (error) {
    // 如果不是JSON，继续处理字符串
  }

  // 去掉开头和结尾的引号
  let cleaned = content.replace(/^"|"$/g, '')

  // 处理转义字符
  cleaned = cleaned.replace(/\\n/g, '\n')  // 换行符
  cleaned = cleaned.replace(/\\"/g, '"')   // 引号
  cleaned = cleaned.replace(/\\t/g, '\t')  // 制表符
  cleaned = cleaned.replace(/\\\\/g, '\\') // 反斜杠

  return cleaned
}

const canGenerateChapter = (chapterNumber: number) => {
  if (!project.value?.blueprint?.chapter_outline) return false

  // 检查前面所有章节是否都已成功生成或处于待确认状态
  const outlines = project.value.blueprint.chapter_outline.sort((a, b) => a.chapter_number - b.chapter_number)

  for (const outline of outlines) {
    if (outline.chapter_number >= chapterNumber) break

    const chapter = project.value?.chapters.find(ch => ch.chapter_number === outline.chapter_number)
    // 允许前一章处于 waiting_for_confirm（待确认）或 successful（已完成）状态时生成下一章
    const allowedStatuses = ['successful', 'waiting_for_confirm']
    if (!chapter || !allowedStatuses.includes(chapter.generation_status || '')) {
      return false // 前面有章节未完成
    }
  }

  // 检查当前章节是否已经完成
  const currentChapter = project.value?.chapters.find(ch => ch.chapter_number === chapterNumber)
  if (currentChapter && currentChapter.generation_status === 'successful') {
    return true // 已完成的章节可以重新生成
  }

  return true // 前面章节都完成了，可以生成当前章节
}

const isChapterFailed = (chapterNumber: number) => {
  if (!project.value?.chapters) return false
  const chapter = project.value.chapters.find(ch => ch.chapter_number === chapterNumber)
  return chapter && chapter.generation_status === 'failed'
}

const hasChapterInProgress = (chapterNumber: number) => {
  if (!project.value?.chapters) return false
  const chapter = project.value.chapters.find(ch => ch.chapter_number === chapterNumber)
  // waiting_for_confirm状态表示等待选择版本 = 进行中状态
  return chapter && chapter.generation_status === 'waiting_for_confirm'
}

// 可用版本列表 (合并生成结果和已有版本)
const availableVersions = computed(() => {
  // 优先使用新生成的版本（对象数组格式）
  if (chapterGenerationResult.value?.versions) {
    console.log('使用生成结果版本:', chapterGenerationResult.value.versions)
    return chapterGenerationResult.value.versions
  }

  // 使用章节已有的版本（字符串数组格式，需要转换为对象数组）
  if (selectedChapter.value?.versions && Array.isArray(selectedChapter.value.versions)) {
    console.log('原始章节版本 (字符串数组):', selectedChapter.value.versions)

    // 将字符串数组转换为ChapterVersion对象数组
    const convertedVersions = selectedChapter.value.versions.map((versionString, index) => {
      console.log(`版本 ${index} 原始字符串:`, versionString)

      try {
        // 解析JSON字符串
        const versionObj = JSON.parse(versionString)
        console.log(`版本 ${index} 解析后的对象:`, versionObj)

        // 提取content字段作为实际内容
        const actualContent = versionObj.content || versionString

        console.log(`版本 ${index} 实际内容:`, actualContent.substring(0, 100) + '...')

        return {
          content: actualContent,
          style: '标准' // 默认风格
        }
      } catch (error) {
        // 如果JSON解析失败，直接使用原始字符串
        console.log(`版本 ${index} JSON解析失败，使用原始字符串:`, error)
        return {
          content: versionString,
          style: '标准'
        }
      }
    })

    console.log('转换后的版本对象:', convertedVersions)
    return convertedVersions
  }

  console.log('没有可用版本，selectedChapter:', selectedChapter.value)
  return []
})


// 方法
const goBack = () => {
  router.push('/workspace')
}

const viewProjectDetail = () => {
  if (project.value) {
    router.push(`/detail/${project.value.id}`)
  }
}

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

const loadProject = async () => {
  try {
    await novelStore.loadProject(props.id)
  } catch (error) {
    console.error('加载项目失败:', error)
  }
}

const refreshProject = async () => {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await novelStore.loadProject(props.id)
    globalAlert.showSuccess('刷新成功', '状态已更新')
  } catch (error) {
    console.error('刷新项目失败:', error)
    globalAlert.showError(`刷新失败: ${error instanceof Error ? error.message : '未知错误'}`, '刷新失败')
  } finally {
    isRefreshing.value = false
  }
}

const fetchChapterStatus = async () => {
  if (selectedChapterNumber.value === null) {
    return
  }
  try {
    await novelStore.loadChapter(selectedChapterNumber.value)
    console.log('Chapter status polled and updated.')
  } catch (error) {
    console.error('轮询章节状态失败:', error)
    // 在这里可以决定是否要通知用户轮询失败
  }
}


// 显示版本详情
const showVersionDetail = (versionIndex: number) => {
  detailVersionIndex.value = versionIndex
  showVersionDetailModal.value = true
}

// 关闭版本详情弹窗
const closeVersionDetail = () => {
  showVersionDetailModal.value = false
}

// 隐藏版本选择器，返回内容视图
const hideVersionSelector = () => {
  // Now controlled by computed property, but we can clear the generation result
  chapterGenerationResult.value = null
  selectedVersionIndex.value = 0
}

const selectChapter = (chapterNumber: number) => {
  selectedChapterNumber.value = chapterNumber
  chapterGenerationResult.value = null
  selectedVersionIndex.value = 0
  closeSidebar()
}

const generateChapter = async (chapterNumber: number) => {
  // 检查是否可以生成该章节
  if (!canGenerateChapter(chapterNumber) && !isChapterFailed(chapterNumber) && !hasChapterInProgress(chapterNumber)) {
    globalAlert.showError('请按顺序生成章节，先完成前面的章节', '生成受限')
    return
  }

  try {
    generatingChapter.value = chapterNumber
    selectedChapterNumber.value = chapterNumber

    // 在本地更新章节状态为generating
    if (project.value?.chapters) {
      const chapter = project.value.chapters.find(ch => ch.chapter_number === chapterNumber)
      if (chapter) {
        chapter.generation_status = 'generating'
      } else {
        // If chapter does not exist, create a temporary one to show generating state
        const outline = project.value.blueprint?.chapter_outline?.find(o => o.chapter_number === chapterNumber)
        project.value.chapters.push({
          chapter_number: chapterNumber,
          title: outline?.title || '加载中...',
          summary: outline?.summary || '',
          content: '',
          versions: [],
          evaluation: null,
          generation_status: 'generating'
        } as Chapter)
      }
    }

    await novelStore.generateChapter(chapterNumber)

    // store 中的 project 已经被更新，所以我们不需要手动修改本地状态
    // chapterGenerationResult 也不再需要，因为 availableVersions 会从更新后的 project.chapters 中获取数据
    // showVersionSelector is now a computed property and will update automatically.
    chapterGenerationResult.value = null
    selectedVersionIndex.value = 0

    // 自动模式处理：生成完成后自动选择最佳版本
    if (autoMode.value && !isBatchGenerating.value) {
      // 从更新后的章节数据中获取版本信息
      const updatedChapter = project.value?.chapters?.find(
        ch => ch.chapter_number === chapterNumber
      )

      if (updatedChapter?.versions && updatedChapter.versions.length > 0) {
        // 查找 AI 推荐的最佳版本索引
        let bestVersionIndex = 0

        for (let i = 0; i < updatedChapter.versions.length; i++) {
          try {
            const versionData = JSON.parse(updatedChapter.versions[i])
            if (versionData.ai_review?.is_best === true) {
              bestVersionIndex = i
              console.log(`AI 推荐最佳版本: 版本 ${i + 1}`)
              break
            }
          } catch (e) {
            // 解析失败，继续检查下一个版本
          }
        }

        console.log(`自动模式：选择版本 ${bestVersionIndex + 1}`)

        // 延迟执行自动选择，确保 UI 更新完成
        setTimeout(async () => {
          try {
            await selectVersion(bestVersionIndex)
            globalAlert.showSuccess(`已自动选择 AI 推荐的版本 ${bestVersionIndex + 1}`, '自动选择')

            // 选择成功后，自动生成下一章
            const nextChapterNumber = chapterNumber + 1
            const hasNextChapter = project.value?.blueprint?.chapter_outline?.some(
              o => o.chapter_number === nextChapterNumber
            )

            if (hasNextChapter) {
              const nextChapter = project.value?.chapters?.find(
                ch => ch.chapter_number === nextChapterNumber
              )
              const nextChapterStatus = nextChapter?.generation_status || 'not_generated'

              if (nextChapterStatus === 'not_generated') {
                console.log(`自动开始生成第 ${nextChapterNumber} 章`)
                setTimeout(() => {
                  generateChapter(nextChapterNumber)
                }, 1000)
              }
            }
          } catch (selectError) {
            console.error('自动选择版本失败:', selectError)
            globalAlert.showError('自动选择版本失败，请手动选择', '自动选择失败')
          }
        }, 500)
      }
    }
  } catch (error) {
    console.error('生成章节失败:', error)

    // 错误状态的本地更新仍然是必要的，以立即反映UI
    if (project.value?.chapters) {
      const chapter = project.value.chapters.find(ch => ch.chapter_number === chapterNumber)
      if (chapter) {
        chapter.generation_status = 'failed'
      }
    }

    globalAlert.showError(`生成章节失败: ${error instanceof Error ? error.message : '未知错误'}`, '生成失败')
  } finally {
    generatingChapter.value = null
  }
}

const regenerateChapter = async () => {
  if (selectedChapterNumber.value !== null) {
    await generateChapter(selectedChapterNumber.value)
  }
}

const selectVersion = async (versionIndex: number) => {
  if (selectedChapterNumber.value === null || !availableVersions.value?.[versionIndex]?.content) {
    return
  }

  try {
    // 在本地立即更新状态以反映UI
    if (project.value?.chapters) {
      const chapter = project.value.chapters.find(ch => ch.chapter_number === selectedChapterNumber.value)
      if (chapter) {
        chapter.generation_status = 'selecting'
      }
    }

    selectedVersionIndex.value = versionIndex
    await novelStore.selectChapterVersion(selectedChapterNumber.value, versionIndex)

    // 状态更新将由 store 自动触发，本地无需手动更新
    // 轮询机制会处理状态变更，成功后会自动隐藏选择器
    // showVersionSelector.value = false
    chapterGenerationResult.value = null
    globalAlert.showSuccess('版本已确认', '操作成功')
  } catch (error) {
    console.error('选择章节版本失败:', error)
    // 错误状态下恢复章节状态
    if (project.value?.chapters) {
      const chapter = project.value.chapters.find(ch => ch.chapter_number === selectedChapterNumber.value)
      if (chapter) {
        chapter.generation_status = 'waiting_for_confirm' // Or the previous state
      }
    }
    globalAlert.showError(`选择章节版本失败: ${error instanceof Error ? error.message : '未知错误'}`, '选择失败')
  }
}

// 从详情弹窗中选择版本
const selectVersionFromDetail = async () => {
  selectedVersionIndex.value = detailVersionIndex.value
  await selectVersion(detailVersionIndex.value)
  closeVersionDetail()
}

const confirmVersionSelection = async () => {
  await selectVersion(selectedVersionIndex.value)
}

const openEditChapterModal = (chapter: ChapterOutline) => {
  editingChapter.value = chapter
  showEditChapterModal.value = true
}

const saveChapterChanges = async (updatedChapter: ChapterOutline) => {
  try {
    await novelStore.updateChapterOutline(updatedChapter)
    globalAlert.showSuccess('章节大纲已更新', '保存成功')
  } catch (error) {
    console.error('更新章节大纲失败:', error)
    globalAlert.showError(`更新章节大纲失败: ${error instanceof Error ? error.message : '未知错误'}`, '保存失败')
  } finally {
    showEditChapterModal.value = false
  }
}

const evaluateChapter = async () => {
  if (selectedChapterNumber.value !== null) {
    // 保存原始状态，用于失败时恢复
    let previousStatus: "not_generated" | "generating" | "evaluating" | "selecting" | "failed" | "evaluation_failed" | "waiting_for_confirm" | "successful" | undefined
    
    try {
      // 在本地更新章节状态为evaluating以立即反映在UI上
      if (project.value?.chapters) {
        const chapter = project.value.chapters.find(ch => ch.chapter_number === selectedChapterNumber.value)
        if (chapter) {
          previousStatus = chapter.generation_status // 保存原状态
          chapter.generation_status = 'evaluating'
        }
      }
      await novelStore.evaluateChapter(selectedChapterNumber.value)
      
      // 评审完成后，状态会通过store和轮询更新，这里不需要额外操作
      globalAlert.showSuccess('章节评审结果已生成', '评审成功')
    } catch (error) {
      console.error('评审章节失败:', error)
      
      // 错误状态下恢复章节状态为原始状态
      if (project.value?.chapters) {
        const chapter = project.value.chapters.find(ch => ch.chapter_number === selectedChapterNumber.value)
        if (chapter && previousStatus) {
          chapter.generation_status = previousStatus // 恢复为原状态
        }
      }
      
      globalAlert.showError(`评审章节失败: ${error instanceof Error ? error.message : '未知错误'}`, '评审失败')
    }
  }
}

const deleteChapter = async (chapterNumbers: number | number[]) => {
  const numbersToDelete = Array.isArray(chapterNumbers) ? chapterNumbers : [chapterNumbers]
  const confirmationMessage = numbersToDelete.length > 1
    ? `您确定要删除选中的 ${numbersToDelete.length} 个章节吗？这个操作无法撤销。`
    : `您确定要删除第 ${numbersToDelete[0]} 章吗？这个操作无法撤销。`

  if (window.confirm(confirmationMessage)) {
    try {
      await novelStore.deleteChapter(numbersToDelete)
      globalAlert.showSuccess('章节已删除', '操作成功')
      // If the currently selected chapter was deleted, unselect it
      if (selectedChapterNumber.value && numbersToDelete.includes(selectedChapterNumber.value)) {
        selectedChapterNumber.value = null
      }
    } catch (error) {
      console.error('删除章节失败:', error)
      globalAlert.showError(`删除章节失败: ${error instanceof Error ? error.message : '未知错误'}`, '删除失败')
    }
  }
}

const generateOutline = async () => {
  showGenerateOutlineModal.value = true
}

const editChapterContent = async (data: { chapterNumber: number, content: string }) => {
  if (!project.value) return

  try {
    await novelStore.editChapterContent(project.value.id, data.chapterNumber, data.content)
    globalAlert.showSuccess('章节内容已更新', '保存成功')
  } catch (error) {
    console.error('编辑章节内容失败:', error)
    globalAlert.showError(`编辑章节内容失败: ${error instanceof Error ? error.message : '未知错误'}`, '保存失败')
  }
}

const handleGenerateOutline = async (numChapters: number) => {
  if (!project.value) return
  isGeneratingOutline.value = true
  try {
    const startChapter = (project.value.blueprint?.chapter_outline?.length || 0) + 1
    await novelStore.generateChapterOutline(startChapter, numChapters)
    globalAlert.showSuccess('新的章节大纲已生成', '操作成功')
  } catch (error) {
    console.error('生成大纲失败:', error)
    globalAlert.showError(`生成大纲失败: ${error instanceof Error ? error.message : '未知错误'}`, '生成失败')
  } finally {
    isGeneratingOutline.value = false
  }
}

// 批量生成章节专用的生成函数（跳过一些确认检查）
const generateChapterForBatch = async (chapterNumber: number) => {
  generatingChapter.value = chapterNumber

  try {
    // 本地更新状态为 generating
    if (project.value?.chapters) {
      const chapter = project.value.chapters.find(ch => ch.chapter_number === chapterNumber)
      if (chapter) {
        chapter.generation_status = 'generating'
      } else {
        // 如果章节不存在，创建一个临时章节以显示生成状态
        const outline = project.value.blueprint?.chapter_outline?.find(o => o.chapter_number === chapterNumber)
        project.value.chapters.push({
          chapter_number: chapterNumber,
          title: outline?.title || '加载中...',
          summary: outline?.summary || '',
          content: '',
          versions: [],
          evaluation: null,
          generation_status: 'generating'
        } as Chapter)
      }
    }

    await novelStore.generateChapter(chapterNumber)
  } finally {
    generatingChapter.value = null
  }
}

// 批量生成章节
const batchGenerateChapters = async (startChapter: number, endChapter: number) => {
  if (isBatchGenerating.value) {
    globalAlert.showError('已有批量生成任务在进行中', '操作失败')
    return
  }

  isBatchGenerating.value = true
  batchGeneratingAbortController.value = new AbortController()

  try {
    // 获取要生成的章节列表（按章节号排序）
    const chapters = project.value?.blueprint?.chapter_outline
      ?.filter(o => o.chapter_number >= startChapter && o.chapter_number <= endChapter)
      ?.sort((a, b) => a.chapter_number - b.chapter_number) || []

    batchGeneratingProgress.value = { current: 0, total: chapters.length }

    for (let i = 0; i < chapters.length; i++) {
      // 检查是否被中止
      if (batchGeneratingAbortController.value?.signal.aborted) {
        globalAlert.showSuccess('批量生成已停止', '操作停止')
        break
      }

      const chapterNumber = chapters[i].chapter_number
      batchGeneratingProgress.value = { current: i + 1, total: chapters.length }

      try {
        // 选中当前生成的章节
        selectedChapterNumber.value = chapterNumber

        // 调用批量生成专用方法
        await generateChapterForBatch(chapterNumber)

        // 刷新项目数据以获取最新状态
        await novelStore.loadProject(props.id)
      } catch (error) {
        console.error(`第 ${chapterNumber} 章生成失败:`, error)
        // 失败时继续生成下一章
        globalAlert.showError(`第 ${chapterNumber} 章生成失败，继续下一章`, '部分失败')
      }
    }

    if (!batchGeneratingAbortController.value?.signal.aborted) {
      globalAlert.showSuccess('批量生成完成！请手动选择各章版本', '生成完成')
    }
  } finally {
    isBatchGenerating.value = false
    batchGeneratingProgress.value = null
    batchGeneratingAbortController.value = null
  }
}

// 停止批量生成
const stopBatchGenerate = () => {
  if (batchGeneratingAbortController.value) {
    batchGeneratingAbortController.value.abort()
  }
}

// 显示批量生成弹窗
const showBatchGenerateModalHandler = () => {
  showBatchGenerateModal.value = true
}

onMounted(() => {
  document.body.classList.add('novel-writing-desk')
  loadProject()
})

onUnmounted(() => {
  document.body.classList.remove('novel-writing-desk')
})
</script>

<style scoped>
/* Writing Desk - Book Page Editing Style */
.writing-desk {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--novel-surface-dim);
  position: relative;
  overflow: hidden;
  animation: desk-appear 0.6s var(--novel-easing-emphasized);
}

@keyframes desk-appear {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Background decorations */
.desk-bg-decoration {
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
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, var(--novel-primary-container) 0%, transparent 70%);
  top: -300px;
  right: -200px;
}

.bg-circle-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, var(--novel-secondary-container) 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
}

.bg-paper-texture {
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.3;
}

/* Main content area */
.desk-content {
  flex: 1;
  width: 100%;
  padding: var(--novel-space-6);
  padding-top: var(--novel-space-4);
  overflow: hidden;
  position: relative;
}

@media (max-width: 640px) {
  .desk-content {
    padding: var(--novel-space-4);
    padding-top: var(--novel-space-3);
  }
}

/* Loading state */
.loading-state {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-card {
  text-align: center;
  padding: var(--novel-space-8);
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  box-shadow: var(--novel-shadow-md);
  position: relative;
  overflow: hidden;
}

.loading-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.4;
  pointer-events: none;
}

.loading-spinner {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--novel-space-4);
  padding: var(--novel-space-4);
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
  border-radius: var(--novel-radius-lg);
  animation: pulse 2s ease-in-out infinite;
}

.spinner-icon {
  width: 100%;
  height: 100%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.95); }
}

.loading-text {
  font-size: var(--novel-text-body);
  color: var(--novel-on-surface-variant);
  position: relative;
}

/* Error state */
.error-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--novel-space-12) 0;
}

.error-card {
  text-align: center;
  padding: var(--novel-space-8);
  max-width: 400px;
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  border: 1px solid var(--novel-outline-variant);
  box-shadow: var(--novel-shadow-md);
  position: relative;
  overflow: hidden;
}

.error-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.4;
  pointer-events: none;
}

.error-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin: 0 auto var(--novel-space-4);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--novel-error-container);
  position: relative;
}

.error-icon {
  width: 24px;
  height: 24px;
  color: var(--novel-error);
}

.error-title {
  font-family: var(--novel-font-heading);
  font-size: var(--novel-text-title);
  font-weight: 600;
  color: var(--novel-on-surface);
  margin-bottom: var(--novel-space-2);
  position: relative;
}

.error-message {
  font-size: var(--novel-text-body);
  color: var(--novel-error);
  margin-bottom: var(--novel-space-6);
  position: relative;
}

/* Main workspace layout */
.desk-main {
  height: 100%;
  display: flex;
  gap: var(--novel-space-6);
}

.desk-workspace {
  flex: 1;
  min-width: 0;
}

/* Novel button styles */
.novel-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-2) var(--novel-space-4);
  border-radius: var(--novel-radius-md);
  font-size: var(--novel-text-label);
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
  position: relative;
}

.novel-btn-tonal {
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
}

.novel-btn-tonal:hover {
  background: var(--novel-primary);
  color: var(--novel-on-primary);
  box-shadow: var(--novel-shadow-sm);
}

/* Line clamp utilities */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--novel-surface-container);
  border-radius: var(--novel-radius-sm);
}

::-webkit-scrollbar-thumb {
  background: var(--novel-outline);
  border-radius: var(--novel-radius-sm);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--novel-on-surface-variant);
}

/* Global body class styles */
:global(body.novel-writing-desk) {
  font-family: var(--novel-font-body);
  color: var(--novel-on-surface);
  background: var(--novel-background);
}

/* Dark mode adjustments */
:root[data-theme="dark"] .loading-card,
:root[data-theme="dark"] .error-card {
  background: var(--novel-surface-container);
}

:root[data-theme="dark"] .loading-card::before,
:root[data-theme="dark"] .error-card::before {
  opacity: 0.2;
}

:root[data-theme="dark"] .bg-circle-1,
:root[data-theme="dark"] .bg-circle-2 {
  opacity: 0.2;
}

/* Responsive */
@media (max-width: 768px) {
  .desk-main {
    gap: var(--novel-space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .writing-desk {
    animation: none;
  }

  .loading-spinner {
    animation: none;
  }
}
</style>
