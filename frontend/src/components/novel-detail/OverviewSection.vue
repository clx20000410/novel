<!-- AIMETA P=概览区_小说基本信息|R=基本信息展示|NR=不含编辑功能|E=component:OverviewSection|X=ui|A=概览组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="overview-section">
    <!-- Core Summary Card -->
    <div class="overview-card">
      <div class="card-header">
        <div>
          <h3 class="card-title-primary">核心摘要</h3>
          <p class="card-subtitle">快速了解项目的定位与调性</p>
        </div>
        <button
          v-if="editable"
          type="button"
          class="edit-btn"
          @click="emitEdit('one_sentence_summary', '核心摘要', data?.one_sentence_summary)">
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      <p class="card-content-primary">{{ data?.one_sentence_summary || '暂无' }}</p>
    </div>

    <!-- Info Grid -->
    <div class="info-grid">
      <div class="info-card">
        <h4 class="info-label">目标受众</h4>
        <p class="info-value">{{ data?.target_audience || '暂无' }}</p>
      </div>
      <div class="info-card">
        <h4 class="info-label">类型</h4>
        <p class="info-value">{{ data?.genre || '暂无' }}</p>
      </div>
      <div class="info-card">
        <h4 class="info-label">风格</h4>
        <p class="info-value">{{ data?.style || '暂无' }}</p>
      </div>
      <div class="info-card">
        <h4 class="info-label">基调</h4>
        <p class="info-value">{{ data?.tone || '暂无' }}</p>
      </div>
    </div>

    <!-- Synopsis Card -->
    <div class="overview-card">
      <div class="card-header">
        <h3 class="card-title">完整剧情梗概</h3>
        <button
          v-if="editable"
          type="button"
          class="edit-btn"
          @click="emitEdit('full_synopsis', '完整剧情梗概', data?.full_synopsis)">
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      <div class="synopsis-content">
        <p>{{ data?.full_synopsis || '暂无' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineEmits, defineProps } from 'vue'

interface OverviewData {
  one_sentence_summary?: string | null
  target_audience?: string | null
  genre?: string | null
  style?: string | null
  tone?: string | null
  full_synopsis?: string | null
}

const props = defineProps<{
  data: OverviewData | null
  editable?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', payload: { field: string; title: string; value: any }): void
}>()

const emitEdit = (field: string, title: string, value: any) => {
  if (!props.editable) return
  emit('edit', { field, title, value })
}
</script>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'OverviewSection'
})
</script>

<style scoped>
.overview-section {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-6, 1.5rem);
}

/* Card Base Styles */
.overview-card {
  background-color: var(--novel-surface-container, var(--md-surface-container));
  border-radius: var(--novel-radius-xl, 1rem);
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  padding: var(--novel-space-6, 1.5rem);
  box-shadow: var(--novel-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
  transition: box-shadow var(--novel-duration-normal, 200ms) var(--novel-easing-standard, ease);
}

.overview-card:hover {
  box-shadow: var(--novel-shadow-md, 0 4px 6px rgba(0, 0, 0, 0.1));
}

/* Card Header */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--novel-space-4, 1rem);
  margin-bottom: var(--novel-space-3, 0.75rem);
}

.card-title-primary {
  font-size: var(--novel-text-label, 0.875rem);
  font-weight: 600;
  color: var(--novel-primary, var(--md-primary));
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.card-title {
  font-size: var(--novel-text-title, 1.125rem);
  font-weight: 600;
  color: var(--novel-on-surface, var(--md-on-surface));
  margin: 0;
}

.card-subtitle {
  font-size: var(--novel-text-caption, 0.75rem);
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  margin: var(--novel-space-1, 0.25rem) 0 0 0;
}

/* Card Content */
.card-content-primary {
  font-size: var(--novel-text-title, 1.125rem);
  line-height: 1.6;
  color: var(--novel-on-surface, var(--md-on-surface));
  min-height: 2.5rem;
  margin: 0;
}

/* Edit Button */
.edit-btn {
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  background: transparent;
  border: none;
  padding: var(--novel-space-2, 0.5rem);
  border-radius: var(--novel-radius-md, 0.5rem);
  cursor: pointer;
  transition: all var(--novel-duration-fast, 150ms) var(--novel-easing-standard, ease);
  flex-shrink: 0;
}

.edit-btn:hover {
  color: var(--novel-primary, var(--md-primary));
  background-color: var(--novel-primary-container, var(--md-primary-container));
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: var(--novel-space-4, 1rem);
}

@media (min-width: 640px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1280px) {
  .info-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.info-card {
  background-color: var(--novel-surface-container, var(--md-surface-container));
  border-radius: var(--novel-radius-xl, 1rem);
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  padding: var(--novel-space-4, 1rem);
  box-shadow: var(--novel-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
  transition: box-shadow var(--novel-duration-normal, 200ms) var(--novel-easing-standard, ease);
}

.info-card:hover {
  box-shadow: var(--novel-shadow-md, 0 4px 6px rgba(0, 0, 0, 0.1));
}

.info-label {
  font-size: var(--novel-text-caption, 0.75rem);
  font-weight: 600;
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--novel-space-2, 0.5rem) 0;
}

.info-value {
  font-size: var(--novel-text-body, 1rem);
  font-weight: 500;
  color: var(--novel-on-surface, var(--md-on-surface));
  min-height: 1.5rem;
  margin: 0;
}

/* Synopsis Content */
.synopsis-content {
  line-height: 1.75;
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  white-space: pre-line;
}

.synopsis-content p {
  margin: 0;
}
</style>
