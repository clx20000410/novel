<!-- AIMETA P=角色区_角色信息展示|R=角色卡片|NR=不含编辑功能|E=component:CharactersSection|X=ui|A=角色组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="characters-section">
    <!-- Header -->
    <div class="section-header">
      <div>
        <h2 class="section-title">主要角色</h2>
        <p class="section-subtitle">了解故事中核心人物的目标与个性</p>
      </div>
      <button
        v-if="editable"
        type="button"
        class="edit-btn"
        @click="emitEdit('characters', '主要角色', data?.characters)">
        <svg class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
          <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
          <path fill-rule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Characters Grid -->
    <div class="characters-grid">
      <article
        v-for="(character, index) in characters"
        :key="index"
        class="character-card">
        <div class="card-content">
          <div class="character-header">
            <div class="avatar">
              {{ character.name?.slice(0, 1) || '角' }}
            </div>
            <div>
              <h3 class="character-name">{{ character.name || '未命名角色' }}</h3>
              <p v-if="character.identity" class="character-identity">{{ character.identity }}</p>
            </div>
          </div>
          <dl class="character-details">
            <div v-if="character.personality">
              <dt class="detail-label">性格</dt>
              <dd class="detail-value">{{ character.personality }}</dd>
            </div>
            <div v-if="character.goals">
              <dt class="detail-label">目标</dt>
              <dd class="detail-value">{{ character.goals }}</dd>
            </div>
            <div v-if="character.abilities">
              <dt class="detail-label">能力</dt>
              <dd class="detail-value">{{ character.abilities }}</dd>
            </div>
            <div v-if="character.relationship_to_protagonist">
              <dt class="detail-label">与主角的关系</dt>
              <dd class="detail-value">{{ character.relationship_to_protagonist }}</dd>
            </div>
          </dl>
        </div>
      </article>
      <div v-if="!characters.length" class="empty-state">
        暂无角色信息
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineEmits, defineProps } from 'vue'

interface CharacterItem {
  name?: string
  identity?: string
  personality?: string
  goals?: string
  abilities?: string
  relationship_to_protagonist?: string
}

const props = defineProps<{
  data: { characters?: CharacterItem[] } | null
  editable?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', payload: { field: string; title: string; value: any }): void
}>()

const characters = computed(() => props.data?.characters || [])

const emitEdit = (field: string, title: string, value: any) => {
  if (!props.editable) return
  emit('edit', { field, title, value })
}
</script>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'CharactersSection'
})
</script>

<style scoped>
.characters-section {
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

.characters-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--novel-space-6, 1.5rem);
}

@media (min-width: 1280px) {
  .characters-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.character-card {
  background-color: var(--novel-surface-container, var(--md-surface-container));
  border-radius: var(--novel-radius-xl, 1rem);
  border: 1px solid var(--novel-outline-variant, var(--md-outline-variant));
  box-shadow: var(--novel-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
  transition: all var(--novel-duration-normal, 200ms) var(--novel-easing-standard, ease);
}

.character-card:hover {
  box-shadow: var(--novel-shadow-lg, 0 10px 15px rgba(0, 0, 0, 0.1));
}

.card-content {
  padding: var(--novel-space-6, 1.5rem);
}

.character-header {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-4, 1rem);
  margin-bottom: var(--novel-space-4, 1rem);
}

@media (min-width: 640px) {
  .character-header {
    flex-direction: row;
    align-items: center;
  }
}

.avatar {
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  background-color: var(--novel-primary-container, var(--md-primary-container));
  color: var(--novel-primary, var(--md-primary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--novel-text-title, 1.125rem);
  font-weight: 600;
  flex-shrink: 0;
}

.character-name {
  font-size: var(--novel-text-title, 1.25rem);
  font-weight: 700;
  color: var(--novel-on-surface, var(--md-on-surface));
  margin: 0;
}

.character-identity {
  font-size: var(--novel-text-body, 0.875rem);
  font-weight: 500;
  color: var(--novel-primary, var(--md-primary));
  margin: var(--novel-space-1, 0.25rem) 0 0 0;
}

.character-details {
  display: flex;
  flex-direction: column;
  gap: var(--novel-space-3, 0.75rem);
  margin: 0;
}

.detail-label {
  font-weight: 600;
  color: var(--novel-on-surface, var(--md-on-surface));
  margin-bottom: var(--novel-space-1, 0.25rem);
  font-size: var(--novel-text-body, 0.875rem);
}

.detail-value {
  color: var(--novel-on-surface-variant, var(--md-on-surface-variant));
  line-height: 1.5;
  margin: 0;
  font-size: var(--novel-text-body, 0.875rem);
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
