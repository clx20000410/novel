<!-- AIMETA P=世界观区_世界设定展示|R=世界观信息|NR=不含编辑功能|E=component:WorldSettingSection|X=ui|A=世界观组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="world-setting-section">
    <!-- Core Rules Card -->
    <div class="setting-card">
      <div class="card-header">
        <h3 class="card-title">核心规则</h3>
        <button
          v-if="editable"
          type="button"
          class="edit-btn"
          @click="emitEdit('world_setting.core_rules', '核心规则', worldSetting.core_rules)">
          <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
            <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      <p class="card-content">{{ worldSetting.core_rules || '暂无' }}</p>
    </div>

    <!-- Locations & Factions Grid -->
    <div class="setting-grid">
      <!-- Key Locations -->
      <div class="setting-card">
        <div class="card-header">
          <div class="card-title-with-icon">
            <svg class="card-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18"/><path d="M6 18H4a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h2v7Z"/><path d="M18 18h2a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2h-2v7Z"/></svg>
            <span>关键地点</span>
          </div>
          <button
            v-if="editable"
            type="button"
            class="edit-btn"
            @click="emitEdit('world_setting.key_locations', '关键地点', worldSetting.key_locations)">
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
              <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
        <ul class="item-list">
          <li v-for="(item, index) in locations" :key="index" class="item-card">
            <strong class="item-title">{{ item.title }}</strong>
            <span class="item-desc">{{ item.description }}</span>
          </li>
          <li v-if="!locations.length" class="empty-text">暂无数据</li>
        </ul>
      </div>

      <!-- Factions -->
      <div class="setting-card">
        <div class="card-header">
          <div class="card-title-with-icon">
            <svg class="card-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            <span>主要阵营</span>
          </div>
          <button
            v-if="editable"
            type="button"
            class="edit-btn"
            @click="emitEdit('world_setting.factions', '主要阵营', worldSetting.factions)">
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
              <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
        <ul class="item-list">
          <li v-for="(item, index) in factions" :key="index" class="item-card">
            <strong class="item-title">{{ item.title }}</strong>
            <span class="item-desc">{{ item.description }}</span>
          </li>
          <li v-if="!factions.length" class="empty-text">暂无数据</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'

interface ListItem {
  title: string
  description: string
}

const props = defineProps<{
  data: Record<string, any> | null
  editable?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', payload: { field: string; title: string; value: any }): void
}>()

const worldSetting = computed(() => props.data?.world_setting || {})

const normalizeList = (source: any): ListItem[] => {
  if (!source) return []
  if (Array.isArray(source)) {
    return source.map((item: any) => {
      if (typeof item === 'string') {
        const [title, ...rest] = item.split('：')
        return {
          title: title || item,
          description: rest.join('：') || '暂无描述'
        }
      }
      return {
        title: item?.name || '未命名',
        description: item?.description || item?.details || '暂无描述'
      }
    })
  }
  return []
}

const locations = computed(() => normalizeList(worldSetting.value?.key_locations))
const factions = computed(() => normalizeList(worldSetting.value?.factions))

const emitEdit = (field: string, title: string, value: any) => {
  if (!props.editable) return
  emit('edit', { field, title, value })
}
</script>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'WorldSettingSection'
})
</script>

<style scoped>
.world-setting-section {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-6, 1.5rem);
}

.setting-card {
  background-color: var(--novel-surface-container, var(--md-surface-container));
  border-radius: var(--novel-radius-xl, 1rem);
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  padding: var(--novel-space-6, 1.5rem);
  box-shadow: var(--novel-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
}

.setting-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--novel-space-6, 1.5rem);
}

@media (min-width: 1024px) {
  .setting-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--novel-space-4, 1rem);
}

.card-title {
  font-size: var(--novel-text-title, 1.125rem);
  font-weight: 600;
  color: var(--novel-on-surface, var(--md-on-surface));
  margin: 0;
}

.card-title-with-icon {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: var(--novel-on-surface, var(--md-on-surface));
}

.card-icon {
  margin-right: var(--novel-space-2, 0.5rem);
  color: var(--novel-primary, var(--md-primary));
}

.edit-btn {
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  background: transparent;
  border: none;
  padding: var(--novel-space-2, 0.5rem);
  border-radius: var(--novel-radius-md, 0.5rem);
  cursor: pointer;
  transition: all var(--novel-duration-fast, 150ms) var(--novel-easing-standard, ease);
}

.edit-btn:hover {
  color: var(--novel-primary, var(--md-primary));
  background-color: var(--novel-primary-container, var(--md-primary-container));
}

.card-content {
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  line-height: 1.75;
  white-space: pre-line;
  margin: 0;
}

.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-4, 1rem);
}

.item-card {
  background-color: var(--novel-surface-container-high, var(--md-surface-container-high));
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  border-radius: var(--novel-radius-lg, 0.75rem);
  padding: var(--novel-space-4, 1rem);
}

.item-title {
  display: block;
  color: var(--novel-on-surface, var(--md-on-surface));
  font-weight: 600;
  margin-bottom: var(--novel-space-1, 0.25rem);
}

.item-desc {
  font-size: var(--novel-text-caption, 0.75rem);
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  line-height: 1.5;
}

.empty-text {
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  font-size: var(--novel-text-body, 0.875rem);
  opacity: 0.7;
}
</style>
