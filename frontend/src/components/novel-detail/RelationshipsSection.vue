<!-- AIMETA P=关系区_角色关系展示|R=关系图谱|NR=不含编辑功能|E=component:RelationshipsSection|X=ui|A=关系组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="relationships-section">
    <!-- Header -->
    <div class="section-header">
      <div>
        <h2 class="section-title">人物关系</h2>
        <p class="section-subtitle">角色之间的纽带与冲突</p>
      </div>
      <button
        v-if="editable"
        type="button"
        class="edit-btn"
        @click="emitEdit('relationships', '人物关系', data?.relationships)">
        <svg class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
          <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
          <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Relationships Grid -->
    <div class="relationships-grid">
      <div
        v-for="(relation, index) in relationships"
        :key="index"
        class="relation-card">
        <div class="relation-header">
          <div class="character-info">
            <div class="avatar avatar-from">
              {{ relation.character_from?.slice(0, 1) || '角' }}
            </div>
            <span class="character-name">{{ relation.character_from || '未知角色' }}</span>
          </div>
          <svg class="arrow-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          <div class="character-info">
            <span class="character-name">{{ relation.character_to || '未知角色' }}</span>
            <div class="avatar avatar-to">
              {{ relation.character_to?.slice(0, 1) || '角' }}
            </div>
          </div>
        </div>
        <div class="relation-detail">
          <p class="relation-type">{{ relation.relationship_type || '关系' }}</p>
          <p class="relation-desc">{{ relation.description || '暂无描述' }}</p>
        </div>
      </div>
      <div v-if="!relationships.length" class="empty-state">
        暂无人际关系信息
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'

interface RelationshipItem {
  character_from?: string
  character_to?: string
  relationship_type?: string
  description?: string
}

const props = defineProps<{
  data: { relationships?: RelationshipItem[] } | null
  editable?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', payload: { field: string; title: string; value: any }): void
}>()

const relationships = computed(() => props.data?.relationships || [])

const emitEdit = (field: string, title: string, value: any) => {
  if (!props.editable) return
  emit('edit', { field, title, value })
}
</script>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'RelationshipsSection'
})
</script>

<style scoped>
.relationships-section {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-6, 1.5rem);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: var(--novel-text-headline, 1.5rem);
  font-weight: 700;
  color: var(--novel-on-surface, var(--md-on-surface));
  margin: 0;
}

.section-subtitle {
  font-size: var(--novel-text-body, 0.875rem);
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  margin: var(--novel-space-1, 0.25rem) 0 0 0;
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

.relationships-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--novel-space-6, 1.5rem);
}

@media (min-width: 768px) {
  .relationships-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.relation-card {
  background-color: var(--novel-surface-container, var(--md-surface-container));
  border-radius: var(--novel-radius-xl, 1rem);
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  box-shadow: var(--novel-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
  padding: var(--novel-space-6, 1.5rem);
}

.relation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.character-info {
  display: flex;
  align-items: center;
  gap: var(--novel-space-3, 0.75rem);
}

.avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.avatar-from {
  background-color: var(--novel-primary-container, var(--md-primary-container));
  color: var(--novel-primary, var(--md-primary));
}

.avatar-to {
  background-color: var(--novel-secondary-container, var(--md-secondary-container));
  color: var(--novel-secondary, var(--md-secondary));
}

.character-name {
  font-weight: 600;
  color: var(--novel-on-surface, var(--md-on-surface));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-icon {
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  flex-shrink: 0;
}

.relation-detail {
  margin-top: var(--novel-space-4, 1rem);
  background-color: var(--novel-surface-container-high, var(--md-surface-container-high));
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  border-radius: var(--novel-radius-lg, 0.75rem);
  padding: var(--novel-space-4, 1rem);
  text-align: center;
}

.relation-type {
  font-size: var(--novel-text-body, 0.875rem);
  font-weight: 600;
  color: var(--novel-on-surface, var(--md-on-surface));
  margin: 0;
}

.relation-desc {
  font-size: var(--novel-text-caption, 0.75rem);
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  line-height: 1.5;
  margin: var(--novel-space-1, 0.25rem) 0 0 0;
}

.empty-state {
  background-color: var(--novel-surface-container, var(--md-surface-container));
  border-radius: var(--novel-radius-xl, 1rem);
  border: 2px dashed var(--novel-outline-variant, var(--md-outline-variant));
  padding: var(--novel-space-10, 2.5rem);
  text-align: center;
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
}
</style>
