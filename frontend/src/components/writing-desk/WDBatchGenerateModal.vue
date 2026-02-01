<!-- AIMETA P=批量生成章节弹窗|R=批量生成配置界面|NR=不含生成逻辑|E=component:WDBatchGenerateModal|X=ui|A=批量生成弹窗|D=vue|S=dom|RD=./README.ai -->
<template>
  <TransitionRoot as="template" :show="show">
    <Dialog as="div" class="relative z-50" @close="$emit('close')">
      <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100" leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0" style="background-color: rgba(0, 0, 0, 0.32);" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" enter-to="opacity-100 translate-y-0 sm:scale-100" leave="ease-in duration-200" leave-from="opacity-100 translate-y-0 sm:scale-100" leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <DialogPanel class="md-dialog m3-batch-dialog text-left transition-all sm:my-6 sm:w-full sm:max-w-lg">
              <div class="px-5 pt-6 pb-5 sm:px-6 sm:pt-6 sm:pb-5">
                <div class="flex flex-col gap-4 sm:flex-row sm:items-start">
                  <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-12 sm:w-12" style="background-color: var(--md-primary-container);">
                    <svg class="h-6 w-6" style="color: var(--md-on-primary-container);" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <div class="text-center sm:flex-1 sm:text-left">
                    <DialogTitle as="h3" class="md-headline-small font-semibold leading-7">批量生成章节</DialogTitle>
                    <div class="mt-2">
                      <p class="md-body-medium md-on-surface-variant">选择要批量生成的章节范围，系统将依次生成每章的两个版本。</p>
                    </div>
                  </div>
                </div>

                <div class="mt-6 space-y-4">
                  <!-- 起始章节选择 -->
                  <div>
                    <label for="startChapter" class="md-text-field-label">起始章节</label>
                    <select
                      id="startChapter"
                      v-model="startChapter"
                      class="md-text-field-input w-full mt-2"
                    >
                      <option
                        v-for="ch in availableChapters"
                        :key="ch.chapter_number"
                        :value="ch.chapter_number"
                      >
                        第 {{ ch.chapter_number }} 章：{{ ch.title }}
                      </option>
                    </select>
                  </div>

                  <!-- 结束章节选择 -->
                  <div>
                    <label for="endChapter" class="md-text-field-label">结束章节</label>
                    <select
                      id="endChapter"
                      v-model="endChapter"
                      class="md-text-field-input w-full mt-2"
                    >
                      <option
                        v-for="ch in availableEndChapters"
                        :key="ch.chapter_number"
                        :value="ch.chapter_number"
                      >
                        第 {{ ch.chapter_number }} 章：{{ ch.title }}
                      </option>
                    </select>
                  </div>

                  <!-- 提示信息 -->
                  <div class="md-card md-card-filled p-4" style="background-color: var(--md-secondary-container); border-radius: var(--md-radius-md);">
                    <div class="flex items-start gap-3">
                      <svg class="w-5 h-5 flex-shrink-0 mt-0.5" style="color: var(--md-on-secondary-container);" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                      </svg>
                      <div>
                        <p class="md-body-medium font-medium" style="color: var(--md-on-secondary-container);">
                          将连续生成 {{ chaptersToGenerate }} 章
                        </p>
                        <p class="md-body-small mt-1" style="color: var(--md-on-secondary-container); opacity: 0.8;">
                          每章生成 2 个版本，生成完成后需要手动选择各章版本。生成过程中可以随时停止。
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="px-6 py-4 sm:flex sm:flex-row-reverse sm:px-8" style="background-color: var(--md-surface-container-low);">
                <button
                  type="button"
                  class="md-btn md-btn-filled md-ripple sm:ml-3 sm:w-auto w-full justify-center"
                  :disabled="chaptersToGenerate < 1"
                  @click="handleGenerate"
                >
                  开始生成
                </button>
                <button
                  type="button"
                  class="md-btn md-btn-outlined md-ripple sm:mt-0 sm:ml-3 sm:w-auto w-full justify-center mt-3"
                  @click="$emit('close')"
                >
                  取消
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue'
import type { ChapterOutline } from '@/api/novel'

interface Props {
  show: boolean
  chapters: ChapterOutline[]
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'generate'])

const startChapter = ref<number>(1)
const endChapter = ref<number>(1)

// 可选的起始章节（按章节号排序）
const availableChapters = computed(() => {
  return [...props.chapters].sort((a, b) => a.chapter_number - b.chapter_number)
})

// 可选的结束章节（必须 >= 起始章节）
const availableEndChapters = computed(() => {
  return availableChapters.value.filter(ch => ch.chapter_number >= startChapter.value)
})

// 计算要生成的章节数
const chaptersToGenerate = computed(() => {
  return Math.max(0, endChapter.value - startChapter.value + 1)
})

// 弹窗打开时初始化默认值
watch(() => props.show, (newVal) => {
  if (newVal && availableChapters.value.length > 0) {
    startChapter.value = availableChapters.value[0].chapter_number
    endChapter.value = availableChapters.value[availableChapters.value.length - 1].chapter_number
  }
})

// 确保结束章节 >= 起始章节
watch(startChapter, (newVal) => {
  if (endChapter.value < newVal) {
    endChapter.value = newVal
  }
})

const handleGenerate = () => {
  if (chaptersToGenerate.value >= 1) {
    emit('generate', startChapter.value, endChapter.value)
    emit('close')
  }
}
</script>

<style scoped>
.m3-batch-dialog {
  border-radius: var(--md-radius-xl);
}
</style>
