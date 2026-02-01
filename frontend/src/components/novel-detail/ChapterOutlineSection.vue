<!-- AIMETA P=章节大纲区_大纲展示|R=大纲列表|NR=不含编辑功能|E=component:ChapterOutlineSection|X=ui|A=大纲组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="outline-title">章节大纲</h2>
        <p class="outline-subtitle">故事结构与章节节奏一目了然</p>
      </div>
      <div v-if="editable" class="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          class="outline-btn outline-btn-primary"
          @click="$emit('add')"
        >
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
          </svg>
          新增章节
        </button>
        <!-- AI 续写大纲按钮 -->
        <button
          type="button"
          class="outline-btn outline-btn-success"
          :disabled="isGenerating"
          @click="showGenerateModal = true"
        >
          <svg v-if="isGenerating" class="h-4 w-4 animate-spin" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z" />
          </svg>
          {{ isGenerating ? '生成中...' : 'AI 续写' }}
        </button>
        <button
          type="button"
          class="outline-btn outline-btn-ghost"
          @click="emitEdit('chapter_outline', '章节大纲', outline)"
        >
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
          编辑大纲
        </button>
        <!-- 刷新按钮 -->
        <button
          type="button"
          class="outline-btn outline-btn-ghost"
          :disabled="isRefreshing"
          @click="$emit('refresh')"
          title="刷新章节大纲"
        >
          <svg
            :class="['h-5 w-5', isRefreshing ? 'animate-spin' : '']"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
          </svg>
          {{ isRefreshing ? '刷新中...' : '刷新' }}
        </button>
      </div>
    </div>

    <!-- AI 续写大纲弹窗 -->
    <div v-if="showGenerateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showGenerateModal = false">
      <div class="outline-modal">
        <div class="px-6 pt-6 pb-4">
          <div class="flex items-center gap-3 mb-4">
            <div class="outline-modal-icon">
              <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M11 17a1 1 0 001.447.894l4-2A1 1 0 0017 15V9.236a1 1 0 00-1.447-.894l-4 2a1 1 0 00-.553.894V17zM15.211 6.276a1 1 0 000-1.788l-4.764-2.382a1 1 0 00-.894 0L4.789 4.488a1 1 0 000 1.788l4.764 2.382a1 1 0 00.894 0l4.764-2.382zM4.447 8.342A1 1 0 003 9.236V15a1 1 0 00.553.894l4 2A1 1 0 009 17v-5.764a1 1 0 00-.553-.894l-4-2z" />
              </svg>
            </div>
            <div>
              <h3 class="outline-modal-title">AI 续写大纲</h3>
              <p class="outline-modal-subtitle">从第 {{ nextChapterNumber }} 章开始续写</p>
            </div>
          </div>
          <div class="space-y-4">
            <div>
              <label class="outline-label">生成章节数</label>
              <input
                type="number"
                v-model.number="numChaptersToGenerate"
                min="1"
                max="50"
                class="outline-input"
              />
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="count in [1, 2, 5, 10, 20]"
                :key="count"
                type="button"
                :class="[
                  'outline-count-btn',
                  numChaptersToGenerate === count ? 'outline-count-btn-active' : ''
                ]"
                @click="numChaptersToGenerate = count"
              >
                {{ count }} 章
              </button>
            </div>
          </div>
        </div>
        <div class="outline-modal-footer">
          <button
            type="button"
            class="outline-btn outline-btn-outlined"
            @click="showGenerateModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="outline-btn outline-btn-success-filled"
            @click="handleGenerate"
          >
            开始生成
          </button>
        </div>
      </div>
    </div>

    <ol class="outline-timeline">
      <li
        v-for="chapter in outline"
        :key="chapter.chapter_number"
        class="ml-6"
      >
        <span class="outline-chapter-badge">
          {{ chapter.chapter_number }}
        </span>
        <div class="outline-chapter-card">
          <div class="flex items-center justify-between gap-4">
            <h3 class="outline-chapter-title">{{ chapter.title || `第${chapter.chapter_number}章` }}</h3>
            <span class="outline-chapter-number">#{{ chapter.chapter_number }}</span>
          </div>
          <p class="outline-chapter-summary">{{ chapter.summary || '暂无摘要' }}</p>
        </div>
      </li>
      <li v-if="!outline.length" class="ml-6 outline-empty">暂无章节大纲</li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import { computed, defineEmits, defineProps, ref } from 'vue'

interface OutlineItem {
  chapter_number: number
  title: string
  summary: string
}

const props = defineProps<{
  outline: OutlineItem[]
  editable?: boolean
  isGenerating?: boolean
  isRefreshing?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', payload: { field: string; title: string; value: any }): void
  (e: 'add'): void
  (e: 'generate', numChapters: number): void
  (e: 'refresh'): void
}>()

const showGenerateModal = ref(false)
const numChaptersToGenerate = ref(5)

const nextChapterNumber = computed(() => {
  if (!props.outline || props.outline.length === 0) return 1
  return Math.max(...props.outline.map(ch => ch.chapter_number)) + 1
})

const emitEdit = (field: string, title: string, value: any) => {
  if (!props.editable) return
  emit('edit', { field, title, value })
}

const handleGenerate = () => {
  if (numChaptersToGenerate.value > 0) {
    emit('generate', numChaptersToGenerate.value)
    showGenerateModal.value = false
  }
}
</script>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ChapterOutlineSection'
})
</script>

<style scoped>
/* 标题样式 */
.outline-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--novel-on-surface);
}

.outline-subtitle {
  font-size: 0.875rem;
  color: var(--novel-on-surface-variant);
}

/* 按钮基础样式 */
.outline-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
}

.outline-btn-primary {
  color: var(--novel-primary);
  background-color: var(--novel-primary-container);
}

.outline-btn-primary:hover {
  filter: brightness(0.95);
}

.outline-btn-success {
  color: var(--novel-success);
  background-color: var(--novel-success-container);
}

.outline-btn-success:hover {
  filter: brightness(0.95);
}

.outline-btn-success-filled {
  color: var(--novel-on-success);
  background-color: var(--novel-success);
}

.outline-btn-success-filled:hover {
  filter: brightness(0.9);
}

.outline-btn-ghost {
  color: var(--novel-on-surface-variant);
  background-color: transparent;
}

.outline-btn-ghost:hover {
  color: var(--novel-primary);
}

.outline-btn-outlined {
  color: var(--novel-on-surface);
  background-color: var(--novel-surface);
  border: 1px solid var(--novel-outline);
}

.outline-btn-outlined:hover {
  background-color: var(--novel-surface-container);
}

/* 弹窗样式 */
.outline-modal {
  background-color: var(--novel-surface);
  border-radius: 1rem;
  box-shadow: var(--novel-shadow-xl);
  width: 100%;
  max-width: 28rem;
  margin: 0 1rem;
  overflow: hidden;
}

.outline-modal-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  background-color: var(--novel-success-container);
  color: var(--novel-success);
  display: flex;
  align-items: center;
  justify-content: center;
}

.outline-modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--novel-on-surface);
}

.outline-modal-subtitle {
  font-size: 0.875rem;
  color: var(--novel-on-surface-variant);
}

.outline-modal-footer {
  padding: 1rem 1.5rem;
  background-color: var(--novel-surface-container);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* 输入框样式 */
.outline-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--novel-on-surface);
  margin-bottom: 0.5rem;
}

.outline-input {
  width: 100%;
  padding: 0.625rem 1rem;
  border: 1px solid var(--novel-outline);
  border-radius: 0.5rem;
  background-color: var(--novel-surface);
  color: var(--novel-on-surface);
  font-size: 0.875rem;
}

.outline-input:focus {
  outline: none;
  border-color: var(--novel-primary);
  box-shadow: 0 0 0 3px rgba(59, 89, 152, 0.12);
}

:root[data-theme="dark"] .outline-input:focus {
  box-shadow: 0 0 0 3px rgba(123, 159, 212, 0.2);
}

/* 章节数量按钮 */
.outline-count-btn {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.5rem;
  border: 1px solid var(--novel-outline);
  background-color: var(--novel-surface);
  color: var(--novel-on-surface);
  cursor: pointer;
  transition: all 0.2s ease;
}

.outline-count-btn:hover {
  background-color: var(--novel-surface-container);
}

.outline-count-btn-active {
  background-color: var(--novel-success);
  color: var(--novel-on-success);
  border-color: var(--novel-success);
}

/* 时间线样式 */
.outline-timeline {
  position: relative;
  border-left: 1px solid var(--novel-outline-variant);
  margin-left: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.outline-chapter-badge {
  position: absolute;
  left: -0.75rem;
  margin-top: 0.25rem;
  display: flex;
  width: 1.5rem;
  height: 1.5rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background-color: var(--novel-primary);
  color: var(--novel-on-primary);
  font-size: 0.75rem;
  font-weight: 600;
}

.outline-chapter-card {
  background-color: var(--novel-surface);
  border-radius: 1rem;
  border: 1px solid var(--novel-outline-variant);
  box-shadow: var(--novel-shadow-sm);
  padding: 1.25rem;
}

.outline-chapter-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--novel-on-surface);
}

.outline-chapter-number {
  font-size: 0.75rem;
  color: var(--novel-on-surface-variant);
}

.outline-chapter-summary {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: var(--novel-on-surface-variant);
  line-height: 1.5;
  white-space: pre-line;
}

.outline-empty {
  font-size: 0.875rem;
  color: var(--novel-on-surface-variant);
}
</style>
