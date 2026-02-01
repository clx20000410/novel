<!-- AIMETA P=版本详情弹窗_版本信息展示|R=版本对比_历史|NR=不含版本管理|E=component:WDVersionDetailModal|X=ui|A=版本弹窗|D=vue|S=dom|RD=./README.ai -->
<template>
  <div v-if="show" class="md-dialog-overlay">
    <div class="md-dialog w-full max-w-4xl m3-detail-dialog">
      <!-- 弹窗头部 -->
      <div class="flex items-center justify-between p-6 border-b" style="border-bottom-color: var(--md-outline-variant);">
        <div>
          <h3 class="md-headline-small font-semibold">版本详情</h3>
          <p class="md-body-small md-on-surface-variant mt-1">
            版本 {{ detailVersionIndex + 1 }}
            <span class="md-on-surface-variant">•</span>
            {{ version?.style || '标准' }}风格
            <span class="md-on-surface-variant">•</span>
            约 {{ Math.round(cleanVersionContent(version?.content || '').length / 100) * 100 }} 字
          </p>
        </div>
        <button
          @click="$emit('close')"
          class="md-icon-btn md-ripple"
        >
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>

      <!-- 弹窗内容 -->
      <div class="p-6 overflow-y-auto max-h-[60vh]">
        <div class="prose max-w-none">
          <div class="whitespace-pre-wrap leading-relaxed" style="color: var(--md-on-surface);">
            {{ cleanVersionContent(version?.content || '') }}
          </div>
        </div>
      </div>

      <!-- 弹窗底部操作按钮 -->
      <div class="flex items-center justify-between p-6 border-t" style="border-top-color: var(--md-outline-variant); background-color: var(--md-surface-container-low);">
        <div class="md-body-small md-on-surface-variant">
          <span v-if="isCurrent" class="md-chip" style="background-color: var(--md-success-container); color: var(--md-on-success-container);">
            <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
            </svg>
            当前选中版本
          </span>
          <span v-else class="md-on-surface-variant">未选中版本</span>
        </div>

        <div class="flex gap-3">
          <button
            @click="$emit('close')"
            class="md-btn md-btn-outlined md-ripple"
          >
            关闭
          </button>
          <button
            v-if="!isCurrent"
            @click="$emit('selectVersion')"
            class="md-btn md-btn-filled md-ripple"
          >
            选择此版本
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChapterVersion } from '@/api/novel'
import { computed } from 'vue'

interface Props {
  show: boolean
  detailVersionIndex: number
  version: ChapterVersion | null
  isCurrent: boolean
}

const props = defineProps<Props>()

defineEmits(['close', 'selectVersion'])

const cleanVersionContent = (content: string): string => {
  if (!content) return ''
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
      content = extracted
    }
  } catch (error) {
    // not a json
  }
  let cleaned = content.replace(/^"|"$/g, '')
  cleaned = cleaned.replace(/\\n/g, '\n')
  cleaned = cleaned.replace(/\\"/g, '"')
  cleaned = cleaned.replace(/\\t/g, '\t')
  cleaned = cleaned.replace(/\\\\/g, '\\')
  return cleaned
}
</script>

<style scoped>
.m3-detail-dialog {
  max-width: min(900px, calc(100vw - 32px));
  max-height: calc(100vh - 32px);
  border-radius: var(--md-radius-xl);
}
</style>
