<!-- AIMETA P=灵感模式_AI对话创作|R=对话创作界面|NR=不含写作台功能|E=route:/inspiration#component:InspirationMode|X=ui|A=对话界面|D=vue|S=dom,net|RD=./README.ai -->
<template>
  <div class="inspiration-mode">
    <!-- Decorative background -->
    <div class="inspiration-bg-decoration">
      <div class="bg-parchment"></div>
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
    </div>

    <div class="inspiration-content">
      <!-- Welcome Screen -->
      <div v-if="!conversationStarted" class="welcome-screen">
        <!-- Book decoration -->
        <div class="welcome-card">
          <div class="card-book-spine"></div>
          <div class="welcome-card-inner">
            <!-- Ornament -->
            <div class="welcome-ornament">
              <span class="ornament-wing"></span>
              <svg class="ornament-quill" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.707 5.293a1 1 0 010 1.414l-1.414 1.414a1 1 0 01-1.414 0L14 4.243 4.929 13.314a2 2 0 00-.499.838l-1.414 4.243a1 1 0 001.213 1.213l4.243-1.414a2 2 0 00.838-.499l9.071-9.071-3.879-3.879-1.414 1.414a1 1 0 11-1.414-1.414L13.414 3l1.293-1.293a1 1 0 011.414 0l4.586 4.586z" />
              </svg>
              <span class="ornament-wing"></span>
            </div>

            <h1 class="novel-display welcome-title">开启你的灵感之旅</h1>
            <p class="novel-body welcome-subtitle">
              {{ isCheckingActiveProject ? '正在检查是否有未完成的灵感...' : '准备好释放你的创造力了吗？让 AI 引导你，一步步构建出独一无二的故事世界。' }}
            </p>

            <button
              @click="startConversation"
              :disabled="novelStore.isLoading || isCheckingActiveProject"
              class="novel-btn novel-btn-filled welcome-btn"
            >
              <svg v-if="isCheckingActiveProject" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              {{ isCheckingActiveProject ? '检查中...' : (novelStore.isLoading ? '正在准备...' : '开启灵感模式') }}
            </button>

            <button @click="goBack" class="novel-btn novel-btn-ghost mt-4">
              返回
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Interface -->
      <div
        v-else-if="!showBlueprintConfirmation && !showBlueprint"
        class="chat-interface"
      >
        <!-- Header -->
        <div class="chat-header">
          <div class="header-left">
            <!-- Quill icon with pulse -->
            <div class="header-quill">
              <span class="quill-pulse"></span>
              <svg class="quill-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.707 5.293a1 1 0 010 1.414l-1.414 1.414a1 1 0 01-1.414 0L14 4.243 4.929 13.314a2 2 0 00-.499.838l-1.414 4.243a1 1 0 001.213 1.213l4.243-1.414a2 2 0 00.838-.499l9.071-9.071-3.879-3.879-1.414 1.414a1 1 0 11-1.414-1.414L13.414 3l1.293-1.293a1 1 0 011.414 0l4.586 4.586z" />
              </svg>
            </div>
            <div>
              <h2 class="novel-title header-title">与"文思"对话中</h2>
              <p class="novel-caption header-subtitle">让灵感在笔尖流淌</p>
            </div>
          </div>
          <div class="header-actions">
            <span v-if="currentTurn > 0" class="turn-badge">
              第 {{ currentTurn }} 轮
            </span>
            <button
              @click="handleRestart"
              class="header-action-btn"
              title="开启新灵感"
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
              </svg>
            </button>
            <button
              @click="exitConversation"
              class="header-action-btn"
              title="返回首页"
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Chat area with parchment styling -->
        <div class="chat-area" ref="chatArea">
          <div class="chat-area-inner">
            <!-- Loading animation -->
            <transition name="fade">
              <InspirationLoading v-if="isInitialLoading" />
            </transition>

            <!-- Chat messages -->
            <ChatBubble
              v-for="(message, index) in chatMessages"
              :key="index"
              :message="message.content"
              :type="message.type"
            />
          </div>
        </div>

        <!-- Input area -->
        <div class="chat-input-area">
          <div class="input-decoration">
            <svg class="ink-bottle" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 2v2H3v6a2 2 0 002 2h6a2 2 0 002-2V4h-4V2H7zm0 4h4v4H5V6h2zm10 0a4 4 0 00-4 4v2h8v-2a4 4 0 00-4-4zm-4 8v6a2 2 0 002 2h4a2 2 0 002-2v-6h-8z" />
            </svg>
          </div>
          <ConversationInput
            :ui-control="currentUIControl"
            :loading="novelStore.isLoading"
            @submit="handleUserInput"
          />
        </div>
      </div>

      <!-- Blueprint Confirmation -->
      <BlueprintConfirmation
        v-if="showBlueprintConfirmation"
        :ai-message="confirmationMessage"
        @blueprint-generated="handleBlueprintGenerated"
        @back="backToConversation"
        @restart="handleRestartFromConfirmation"
      />

      <!-- Blueprint Display -->
      <BlueprintDisplay
        v-if="showBlueprint"
        :blueprint="completedBlueprint"
        :ai-message="blueprintMessage"
        @confirm="handleConfirmBlueprint"
        @regenerate="handleRegenerateBlueprint"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/stores/novel'
import { NovelAPI, type UIControl, type Blueprint } from '@/api/novel'
import ChatBubble from '@/components/ChatBubble.vue'
import ConversationInput from '@/components/ConversationInput.vue'
import BlueprintConfirmation from '@/components/BlueprintConfirmation.vue'
import BlueprintDisplay from '@/components/BlueprintDisplay.vue'
import InspirationLoading from '@/components/InspirationLoading.vue'
import { globalAlert } from '@/composables/useAlert'

interface ChatMessage {
  content: string
  type: 'user' | 'ai'
}

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()

const conversationStarted = ref(false)
const isInitialLoading = ref(false)
const isCheckingActiveProject = ref(true) // 检查活跃项目时的加载状态
const showBlueprintConfirmation = ref(false)
const showBlueprint = ref(false)
const chatMessages = ref<ChatMessage[]>([])
const currentUIControl = ref<UIControl | null>(null)
const currentTurn = ref(0)
const completedBlueprint = ref<Blueprint | null>(null)
const confirmationMessage = ref('')
const blueprintMessage = ref('')
const chatArea = ref<HTMLElement>()

const goBack = () => {
  router.push('/')
}

const resetInspirationMode = () => {
  conversationStarted.value = false
  isInitialLoading.value = false
  isCheckingActiveProject.value = false
  showBlueprintConfirmation.value = false
  showBlueprint.value = false
  chatMessages.value = []
  currentUIControl.value = null
  currentTurn.value = 0
  completedBlueprint.value = null
  confirmationMessage.value = ''
  blueprintMessage.value = ''

  novelStore.setCurrentProject(null)
  novelStore.currentConversationState = {}
}

const exitConversation = async () => {
  const confirmed = await globalAlert.showConfirm('确定要退出灵感模式吗？当前进度会自动保存，可在工作台继续。', '退出确认')
  if (confirmed) {
    resetInspirationMode()
    router.push('/')
  }
}

const handleRestart = async () => {
  const confirmed = await globalAlert.showConfirm('确定要放弃当前灵感并开启新灵感吗？放弃后该灵感将不可继续。', '开启新灵感确认')
  if (confirmed) {
    await startConversationInternal({ forceNew: true })
  }
}

const backToConversation = () => {
  showBlueprintConfirmation.value = false
}

const handleRestartFromConfirmation = async () => {
  // 直接开启新灵感（确认对话框已经在 BlueprintConfirmation 组件中显示过了）
  await startConversationInternal({ forceNew: true })
}

const startConversationInternal = async (options: { forceNew?: boolean } = {}) => {
  resetInspirationMode()
  conversationStarted.value = true
  isInitialLoading.value = true

  try {
    await novelStore.createProject('未命名灵感', '开始灵感模式', options)
    await handleUserInput(null)
  } catch (error) {
    console.error('启动灵感模式失败:', error)
    const detail = (error as any)?.detail
    const projectId = typeof detail === 'object' ? detail?.project_id : null
    if ((detail as any)?.message === 'active_inspiration_exists' && projectId) {
      await router.replace(`/inspiration?project_id=${projectId}`)
      await restoreConversation(projectId)
      return
    }

    globalAlert.showError(`无法开始灵感模式: ${error instanceof Error ? error.message : '未知错误'}`, '启动失败')
    resetInspirationMode()
  }
}

const startConversation = async (_event?: MouseEvent) => {
  await startConversationInternal()
}

const restoreConversation = async (projectId: string) => {
  isCheckingActiveProject.value = true
  try {
    await novelStore.loadProject(projectId)
    const project = novelStore.currentProject
    if (project?.status === 'blueprint_ready') {
      router.replace(`/novel/${project.id}`)
      return
    }
    if (project?.status === 'concept_abandoned') {
      globalAlert.showError('该灵感已被放弃，无法继续。', '无法继续')
      resetInspirationMode()
      return
    }
    // 特殊处理：concept_complete 状态应该直接进入蓝图确认界面
    if (project?.status === 'concept_complete') {
      conversationStarted.value = true
      // 尝试恢复聊天记录用于显示
      if (project.conversation_history && project.conversation_history.length > 0) {
        chatMessages.value = project.conversation_history.map((item): ChatMessage | null => {
          if (item.role === 'user') {
            try {
              const userInput = JSON.parse(item.content)
              return { content: userInput.value, type: 'user' }
            } catch {
              return { content: item.content, type: 'user' }
            }
          } else {
            try {
              const assistantOutput = JSON.parse(item.content)
              return { content: assistantOutput.ai_message, type: 'ai' }
            } catch {
              return { content: item.content, type: 'ai' }
            }
          }
        }).filter((msg): msg is ChatMessage => msg !== null && msg.content !== null)
        currentTurn.value = project.conversation_history.filter(m => m.role === 'assistant').length
      }
      // 直接显示蓝图确认界面
      confirmationMessage.value = '灵感对话已完成！请点击下方按钮生成小说蓝图，或者点击右上角重新开始。'
      showBlueprintConfirmation.value = true
      return
    }
    if (project && project.conversation_history) {
      conversationStarted.value = true

      if (project.conversation_history.length === 0) {
        isInitialLoading.value = true
        await handleUserInput(null)
        return
      }

      chatMessages.value = project.conversation_history.map((item): ChatMessage | null => {
        if (item.role === 'user') {
          try {
            const userInput = JSON.parse(item.content)
            return { content: userInput.value, type: 'user' }
          } catch {
            return { content: item.content, type: 'user' }
          }
        } else {
          try {
            const assistantOutput = JSON.parse(item.content)
            return { content: assistantOutput.ai_message, type: 'ai' }
          } catch {
            return { content: item.content, type: 'ai' }
          }
        }
      }).filter((msg): msg is ChatMessage => msg !== null && msg.content !== null)

      const lastAssistantMsgStr = project.conversation_history.filter(m => m.role === 'assistant').pop()?.content
      if (lastAssistantMsgStr) {
        try {
          const lastAssistantMsg = JSON.parse(lastAssistantMsgStr)

          if (lastAssistantMsg.is_complete) {
            confirmationMessage.value = lastAssistantMsg.ai_message
            showBlueprintConfirmation.value = true
          } else {
            currentUIControl.value = lastAssistantMsg.ui_control
          }
        } catch (parseError) {
          console.warn('解析最后一条AI消息失败:', parseError)
          // 如果对话数据损坏但状态是进行中，允许继续对话
          // currentUIControl 保持为 null，用户可以自由输入
        }
      }
      currentTurn.value = project.conversation_history.filter(m => m.role === 'assistant').length
      await scrollToBottom()
    }
  } catch (error) {
    console.error('恢复对话失败:', error)
    globalAlert.showError(`无法恢复对话: ${error instanceof Error ? error.message : '未知错误'}`, '加载失败')
    resetInspirationMode()
  } finally {
    isCheckingActiveProject.value = false
  }
}

const handleUserInput = async (userInput: any) => {
  try {
    const status = novelStore.currentProject?.status
    if (status === 'blueprint_ready' && novelStore.currentProject) {
      router.replace(`/novel/${novelStore.currentProject.id}`)
      return
    }
    if (status === 'concept_complete') {
      globalAlert.showError('当前灵感对话已完成，无法继续对话。', '已完成')
      return
    }
    if (status === 'concept_abandoned') {
      globalAlert.showError('该灵感已被放弃，无法继续。', '无法继续')
      resetInspirationMode()
      return
    }

    if (userInput && userInput.value) {
      chatMessages.value.push({
        content: userInput.value,
        type: 'user'
      })
      await scrollToBottom()
    }

    const response = await novelStore.sendConversation(userInput)

    if (isInitialLoading.value) {
      isInitialLoading.value = false
    }

    chatMessages.value.push({
      content: response.ai_message,
      type: 'ai'
    })
    currentTurn.value++

    await scrollToBottom()

    if (response.is_complete && response.ready_for_blueprint) {
      if (novelStore.currentProject) {
        novelStore.currentProject.status = 'concept_complete'
      }
      confirmationMessage.value = response.ai_message
      showBlueprintConfirmation.value = true
    } else if (response.is_complete) {
      await handleGenerateBlueprint()
    } else {
      currentUIControl.value = response.ui_control
    }
  } catch (error) {
    console.error('对话失败:', error)
    if (isInitialLoading.value) {
      isInitialLoading.value = false
    }
    globalAlert.showError(`抱歉，与AI连接时遇到问题: ${error instanceof Error ? error.message : '未知错误'}`, '通信失败')
    resetInspirationMode()
  }
}

const handleGenerateBlueprint = async () => {
  try {
    const response = await novelStore.generateBlueprint()
    handleBlueprintGenerated(response)
  } catch (error) {
    console.error('生成蓝图失败:', error)
    globalAlert.showError(`生成蓝图失败: ${error instanceof Error ? error.message : '未知错误'}`, '生成失败')
  }
}

const handleBlueprintGenerated = (response: any) => {
  console.log('收到蓝图生成完成事件:', response)
  completedBlueprint.value = response.blueprint
  blueprintMessage.value = response.ai_message
  showBlueprintConfirmation.value = false
  showBlueprint.value = true
}

const handleRegenerateBlueprint = () => {
  showBlueprint.value = false
  showBlueprintConfirmation.value = true
}

const handleConfirmBlueprint = async () => {
  if (!completedBlueprint.value) {
    globalAlert.showError('蓝图数据缺失，请重新生成或稍后重试。', '保存失败')
    return
  }
  try {
    await novelStore.saveBlueprint(completedBlueprint.value)
    if (novelStore.currentProject) {
      router.push(`/novel/${novelStore.currentProject.id}`)
    }
  } catch (error) {
    console.error('保存蓝图失败:', error)
    globalAlert.showError(`保存蓝图失败: ${error instanceof Error ? error.message : '未知错误'}`, '保存失败')
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}

const restoreActiveInspiration = async () => {
  isCheckingActiveProject.value = true
  try {
    const response = await NovelAPI.getActiveInspiration()
    const project = response.project
    if (project?.id) {
      await router.replace(`/inspiration?project_id=${project.id}`)
      await restoreConversation(project.id)
      return
    }
  } catch (error) {
    console.error('加载灵感记录失败:', error)
  } finally {
    isCheckingActiveProject.value = false
  }
  resetInspirationMode()
}

onMounted(() => {
  const projectId = route.query.project_id as string
  if (projectId) {
    restoreConversation(projectId)
  } else {
    restoreActiveInspiration()
  }
})
</script>

<style scoped>
.inspiration-mode {
  min-height: 100vh;
  padding: var(--novel-space-4);
  background: var(--novel-surface-dim);
  position: relative;
  overflow: hidden;
}

/* Background decorations */
.inspiration-bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-parchment {
  position: absolute;
  inset: 0;
  background: var(--novel-parchment);
  opacity: 0.3;
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
  left: -150px;
}

.bg-circle-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, var(--novel-tertiary-container) 0%, transparent 70%);
  bottom: -150px;
  right: -150px;
}

/* Main content */
.inspiration-content {
  position: relative;
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  min-height: calc(100vh - var(--novel-space-8));
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Welcome screen */
.welcome-screen {
  width: 100%;
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

.welcome-card {
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

.welcome-card-inner {
  padding: var(--novel-space-12) var(--novel-space-8);
  padding-left: calc(var(--novel-space-8) + 20px);
  text-align: center;
  position: relative;
}

.welcome-card-inner::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.4;
  pointer-events: none;
}

.welcome-ornament {
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
  width: 36px;
  height: 36px;
}

.welcome-title {
  color: var(--novel-on-surface);
  margin-bottom: var(--novel-space-4);
  position: relative;
}

.welcome-subtitle {
  color: var(--novel-on-surface-variant);
  max-width: 500px;
  margin: 0 auto var(--novel-space-8);
  line-height: 1.6;
  position: relative;
}

.welcome-btn {
  position: relative;
}

/* Chat interface */
.chat-interface {
  width: 100%;
  height: calc(100vh - var(--novel-space-8));
  max-height: 900px;
  display: flex;
  flex-direction: column;
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  box-shadow: var(--novel-shadow-lg);
  overflow: hidden;
  animation: content-appear 0.6s var(--novel-easing-emphasized);
}

/* Chat header */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--novel-space-4) var(--novel-space-6);
  background: var(--novel-surface);
  border-bottom: 1px solid var(--novel-outline-variant);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--novel-space-3);
}

.header-quill {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--novel-primary-container);
  border-radius: var(--novel-radius-lg);
}

.quill-pulse {
  position: absolute;
  inset: 0;
  border-radius: var(--novel-radius-lg);
  background: var(--novel-primary);
  opacity: 0.3;
  animation: pulse 2s ease-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.2);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

.quill-icon {
  width: 20px;
  height: 20px;
  color: var(--novel-on-primary-container);
  position: relative;
}

.header-title {
  color: var(--novel-on-surface);
  margin: 0;
}

.header-subtitle {
  color: var(--novel-on-surface-variant);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--novel-space-3);
}

.turn-badge {
  padding: var(--novel-space-1) var(--novel-space-3);
  background: var(--novel-surface-container);
  color: var(--novel-on-surface-variant);
  border-radius: var(--novel-radius-full);
  font-size: var(--novel-text-caption);
  font-weight: 500;
}

.header-action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--novel-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.header-action-btn:hover {
  background: var(--novel-surface-container);
  color: var(--novel-primary);
}

/* Chat area */
.chat-area {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

.chat-area::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.3;
  pointer-events: none;
}

.chat-area-inner {
  padding: var(--novel-space-6);
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-4);
  position: relative;
}

/* Chat input area */
.chat-input-area {
  padding: var(--novel-space-4) var(--novel-space-6);
  background: var(--novel-surface-container);
  border-top: 1px solid var(--novel-outline-variant);
  position: relative;
}

.input-decoration {
  position: absolute;
  left: var(--novel-space-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--novel-on-surface-variant);
  opacity: 0.4;
  display: none;
}

.ink-bottle {
  width: 24px;
  height: 24px;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--novel-duration-normal) var(--novel-easing-standard);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Spin animation for loading state */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .inspiration-mode {
    padding: var(--novel-space-2);
  }

  .inspiration-content {
    min-height: calc(100vh - var(--novel-space-4));
  }

  .welcome-card-inner {
    padding: var(--novel-space-8) var(--novel-space-4);
    padding-left: calc(var(--novel-space-4) + 16px);
  }

  .card-book-spine {
    width: 16px;
  }

  .welcome-ornament {
    display: none;
  }

  .chat-interface {
    height: calc(100vh - var(--novel-space-4));
    border-radius: var(--novel-radius-lg);
  }

  .chat-header {
    padding: var(--novel-space-3) var(--novel-space-4);
  }

  .header-subtitle {
    display: none;
  }

  .chat-area-inner {
    padding: var(--novel-space-4);
  }

  .chat-input-area {
    padding: var(--novel-space-3) var(--novel-space-4);
  }
}
</style>
