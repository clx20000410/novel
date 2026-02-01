<!-- AIMETA P=项目卡片_小说项目展示|R=项目信息卡片|NR=不含编辑功能|E=component:ProjectCard|X=internal|A=卡片组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="book-card" :class="bookColorClass" @click="$emit('continue', project)">
    <!-- Book spine -->
    <div class="book-spine">
      <span class="spine-title">{{ truncatedTitle }}</span>
    </div>

    <!-- Book cover -->
    <div class="book-cover">
      <!-- Paper texture overlay -->
      <div class="cover-texture"></div>

      <!-- Bookmark decoration -->
      <div class="book-bookmark">
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      </div>

      <!-- Cover content -->
      <div class="cover-content">
        <!-- Genre badge -->
        <div class="genre-badge" v-if="project.genre">
          {{ project.genre }}
        </div>

        <!-- Book title -->
        <h3 class="book-title" @click.stop="$emit('detail', project.id)">
          {{ project.title }}
        </h3>

        <!-- Status text -->
        <p class="book-status">{{ getStatusText }}</p>

        <!-- Progress bookmark -->
        <div class="progress-bookmark">
          <div class="bookmark-ribbon">
            <span class="bookmark-text">{{ progress }}%</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ height: `${progress}%` }"></div>
          </div>
        </div>

        <!-- Chapter info -->
        <div class="chapter-info" v-if="chapterCount > 0">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>{{ chapterCount }} 章</span>
        </div>

        <!-- Last edited -->
        <p class="book-date">{{ formatDateTime(project.last_edited) }}</p>
      </div>

      <!-- Action buttons - appear on hover -->
      <div class="book-actions">
        <button
          @click.stop="$emit('detail', project.id)"
          class="action-btn"
          title="查看详情"
          aria-label="查看详情"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </button>
        <button
          @click.stop="$emit('export', project)"
          class="action-btn"
          title="导出 JSON"
          aria-label="导出 JSON"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 9l-3 3 3 3M16 9l3 3-3 3" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M14 7l-4 10" />
          </svg>
        </button>
        <button
          @click.stop="$emit('exportTxt', project)"
          class="action-btn"
          title="导出 TXT"
          aria-label="导出 TXT"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M14 2v6h6" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 13H8M16 17H8" />
          </svg>
        </button>
        <button
          @click.stop="handleDelete"
          class="action-btn action-btn-danger"
          title="删除"
          aria-label="删除"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
        <button
          @click.stop="$emit('continue', project)"
          class="action-btn action-btn-primary"
          title="继续创作"
          aria-label="继续创作"
        >
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Book shadow -->
    <div class="book-shadow"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NovelProjectSummary } from '@/api/novel'
import { formatDateTime } from '@/utils/date'

interface Props {
  project: NovelProjectSummary
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'click', id: string): void
  (e: 'detail', id: string): void
  (e: 'continue', project: NovelProjectSummary): void
  (e: 'delete', id: string): void
  (e: 'export', project: NovelProjectSummary): void
  (e: 'exportTxt', project: NovelProjectSummary): void
}>()

// Truncated title for spine
const truncatedTitle = computed(() => {
  const title = props.project.title || ''
  return title.length > 8 ? title.slice(0, 8) + '...' : title
})

// Book color theme based on genre
const bookColorClass = computed(() => {
  const genre = props.project.genre || ''

  if (genre.includes('科幻') || genre.includes('悬疑')) {
    return 'book-theme-blue'
  } else if (genre.includes('奇幻') || genre.includes('冒险')) {
    return 'book-theme-green'
  } else if (genre.includes('穿越') || genre.includes('言情')) {
    return 'book-theme-rose'
  } else if (genre.includes('东方') || genre.includes('武侠')) {
    return 'book-theme-amber'
  }

  return 'book-theme-default'
})

// Progress calculation
const progress = computed(() => {
  const { completed_chapters, total_chapters } = props.project
  return total_chapters > 0 ? Math.round((completed_chapters / total_chapters) * 100) : 0
})

const getStatusText = computed(() => {
  const status = props.project.status
  const { completed_chapters, total_chapters } = props.project

  if (status === 'concept_abandoned') {
    return '已放弃'
  }
  if (status === 'concept_complete') {
    return '灵感已完成'
  }
  if (status === 'concept_in_progress' || status === 'draft') {
    return '灵感进行中'
  }
  if (status === 'blueprint_ready') {
    if (completed_chapters > 0) {
      return `${completed_chapters}/${total_chapters} 章`
    }
    if (total_chapters > 0) {
      return '准备创作'
    }
    return '蓝图就绪'
  }

  if (completed_chapters > 0) {
    return `${completed_chapters}/${total_chapters} 章`
  }
  if (total_chapters > 0) {
    return '准备创作'
  }
  return '蓝图就绪'
})

const chapterCount = computed(() => {
  return props.project.total_chapters
})

const handleDelete = () => {
  emit('delete', props.project.id)
}
</script>

<style scoped>
/* Book Card Container */
.book-card {
  position: relative;
  display: flex;
  min-height: 220px;
  cursor: pointer;
  transition: transform var(--novel-duration-normal) var(--novel-easing-emphasized),
              z-index 0s;
  z-index: 1;
}

.book-card:hover {
  transform: translateY(-6px);
  z-index: 10;
}

/* Book Spine */
.book-spine {
  width: 28px;
  min-height: 220px;
  background: var(--book-spine-color, var(--novel-book-spine));
  border-radius: var(--novel-radius-sm) 0 0 var(--novel-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset -2px 0 4px rgba(0, 0, 0, 0.2);
  position: relative;
}

.spine-title {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  color: rgba(255, 255, 255, 0.9);
  font-size: var(--novel-text-caption);
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.1em;
  padding: var(--novel-space-2) 0;
}

/* Book Cover */
.book-cover {
  flex: 1;
  min-height: 220px;
  background: var(--book-cover-color, var(--novel-surface));
  border-radius: 0 var(--novel-radius-md) var(--novel-radius-md) 0;
  box-shadow: var(--novel-shadow-md);
  position: relative;
  overflow: visible;
  transition: box-shadow var(--novel-duration-fast) var(--novel-easing-standard);
}

.book-card:hover .book-cover {
  box-shadow: var(--novel-shadow-lg);
}

.cover-texture {
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.4;
  pointer-events: none;
}

/* Bookmark decoration */
.book-bookmark {
  position: absolute;
  top: -6px;
  right: var(--novel-space-4);
  color: var(--book-accent-color, var(--novel-primary));
  opacity: 0.8;
  transition: transform var(--novel-duration-fast) var(--novel-easing-standard);
  z-index: 2;
}

.book-card:hover .book-bookmark {
  transform: translateY(4px);
}

/* Cover content */
.cover-content {
  position: relative;
  padding: var(--novel-space-5);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 220px;
}

/* Genre badge */
.genre-badge {
  display: inline-flex;
  align-self: flex-start;
  padding: var(--novel-space-1) var(--novel-space-3);
  background: var(--book-accent-container, var(--novel-primary-container));
  color: var(--book-accent-on-container, var(--novel-on-primary-container));
  border-radius: var(--novel-radius-full);
  font-size: var(--novel-text-caption);
  font-weight: 500;
  margin-bottom: var(--novel-space-3);
}

/* Book title */
.book-title {
  font-family: var(--novel-font-heading);
  font-size: var(--novel-text-title);
  font-weight: 600;
  color: var(--novel-on-surface);
  margin: 0 0 var(--novel-space-2);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  cursor: pointer;
  transition: color var(--novel-duration-fast);
}

.book-title:hover {
  color: var(--novel-primary);
}

/* Status */
.book-status {
  font-size: var(--novel-text-label);
  color: var(--novel-on-surface-variant);
  margin: 0 0 auto;
}

/* Progress bookmark */
.progress-bookmark {
  position: absolute;
  right: var(--novel-space-4);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--novel-space-1);
}

.bookmark-ribbon {
  padding: var(--novel-space-1) var(--novel-space-2);
  background: var(--book-accent-color, var(--novel-primary));
  color: var(--novel-on-primary);
  border-radius: var(--novel-radius-sm);
  font-size: 11px;
  font-weight: 600;
}

.progress-track {
  width: 6px;
  height: 60px;
  background: var(--novel-surface-container);
  border-radius: var(--novel-radius-full);
  overflow: hidden;
  position: relative;
}

.progress-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--book-accent-color, var(--novel-primary));
  border-radius: var(--novel-radius-full);
  transition: height var(--novel-duration-normal) var(--novel-easing-emphasized);
}

/* Chapter info */
.chapter-info {
  display: flex;
  align-items: center;
  gap: var(--novel-space-1);
  color: var(--novel-on-surface-variant);
  font-size: var(--novel-text-caption);
  margin-top: var(--novel-space-3);
}

/* Date */
.book-date {
  font-size: var(--novel-text-caption);
  color: var(--novel-on-surface-variant);
  margin: var(--novel-space-2) 0 0;
  opacity: 0.7;
}

/* Action buttons */
.book-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: var(--novel-space-1);
  padding: var(--novel-space-3);
  background: linear-gradient(transparent, var(--novel-surface-container));
  opacity: 0;
  transform: translateY(8px);
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
  z-index: 10;
  border-radius: 0 0 var(--novel-radius-md) 0;
}

.book-card:hover .book-actions {
  opacity: 1;
  transform: translateY(0);
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--novel-surface);
  color: var(--novel-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
  box-shadow: var(--novel-shadow-sm);
}

.action-btn:hover {
  background: var(--novel-surface-container-high);
  transform: scale(1.1);
}

.action-btn-primary {
  background: var(--novel-primary);
  color: var(--novel-on-primary);
}

.action-btn-primary:hover {
  background: var(--novel-primary-dark);
}

.action-btn-danger:hover {
  background: var(--novel-error-container);
  color: var(--novel-error);
}

/* Book shadow */
.book-shadow {
  position: absolute;
  bottom: -10px;
  left: 10px;
  right: 10px;
  height: 20px;
  background: radial-gradient(ellipse at center, rgba(0, 0, 0, 0.2) 0%, transparent 70%);
  opacity: 0;
  transition: opacity var(--novel-duration-fast);
}

.book-card:hover .book-shadow {
  opacity: 1;
}

/* Theme variations */
.book-theme-default {
  --book-spine-color: var(--novel-book-spine);
  --book-accent-color: var(--novel-primary);
  --book-accent-container: var(--novel-primary-container);
  --book-accent-on-container: var(--novel-on-primary-container);
}

.book-theme-blue {
  --book-spine-color: linear-gradient(180deg, #3B82F6 0%, #1D4ED8 100%);
  --book-accent-color: #3B82F6;
  --book-accent-container: #DBEAFE;
  --book-accent-on-container: #1E40AF;
}

.book-theme-green {
  --book-spine-color: linear-gradient(180deg, #22C55E 0%, #16A34A 100%);
  --book-accent-color: #22C55E;
  --book-accent-container: #DCFCE7;
  --book-accent-on-container: #166534;
}

.book-theme-rose {
  --book-spine-color: linear-gradient(180deg, #F43F5E 0%, #E11D48 100%);
  --book-accent-color: #F43F5E;
  --book-accent-container: #FFE4E6;
  --book-accent-on-container: #BE123C;
}

.book-theme-amber {
  --book-spine-color: linear-gradient(180deg, #F59E0B 0%, #D97706 100%);
  --book-accent-color: #F59E0B;
  --book-accent-container: #FEF3C7;
  --book-accent-on-container: #92400E;
}

/* Dark mode adjustments */
:root[data-theme="dark"] .book-theme-blue {
  --book-accent-container: #1E3A5F;
  --book-accent-on-container: #93C5FD;
}

:root[data-theme="dark"] .book-theme-green {
  --book-accent-container: #14532D;
  --book-accent-on-container: #86EFAC;
}

:root[data-theme="dark"] .book-theme-rose {
  --book-accent-container: #4C0519;
  --book-accent-on-container: #FDA4AF;
}

:root[data-theme="dark"] .book-theme-amber {
  --book-accent-container: #451A03;
  --book-accent-on-container: #FCD34D;
}

/* Responsive */
@media (max-width: 640px) {
  .book-card {
    min-height: 180px;
  }

  .book-spine {
    width: 20px;
    min-height: 180px;
  }

  .book-cover {
    min-height: 180px;
  }

  .cover-content {
    padding: var(--novel-space-4);
    min-height: 180px;
  }

  .book-title {
    font-size: var(--novel-text-body);
  }

  .progress-bookmark {
    right: var(--novel-space-3);
  }

  .progress-track {
    height: 40px;
  }

  .book-actions {
    gap: var(--novel-space-1);
    padding: var(--novel-space-2);
  }

  .action-btn {
    width: 32px;
    height: 32px;
  }

  .book-card:hover {
    transform: translateY(-4px);
  }
}
</style>
