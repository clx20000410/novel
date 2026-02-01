<!-- AIMETA P=评审详情弹窗_章节评审展示|R=评审结果展示|NR=不含评审逻辑|E=component:WDEvaluationDetailModal|X=ui|A=评审弹窗|D=vue|S=dom|RD=./README.ai -->
<template>
  <div v-if="show" class="md-dialog-overlay">
    <div class="md-dialog w-full max-w-4xl m3-eval-dialog flex flex-col">
      <!-- 弹窗头部 -->
      <div class="flex items-center justify-between p-6 border-b" style="border-bottom-color: var(--md-outline-variant);">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style="background-color: var(--md-secondary);">
                <svg class="w-6 h-6" style="color: var(--md-on-secondary);" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-1.707 1.707A1 1 0 003 15v1a1 1 0 001 1h12a1 1 0 001-1v-1a1 1 0 00-.293-.707L16 11.586V8a6 6 0 00-6-6zM8.05 17a2 2 0 103.9 0H8.05z"></path>
                </svg>
            </div>
            <h3 class="md-headline-small font-semibold">AI 评审详情</h3>
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
      <div class="p-6 overflow-y-auto max-h-[calc(80vh-130px)]">
        <div v-if="parsedEvaluation" class="space-y-6 text-sm">
            <div class="md-card md-card-filled p-4" style="border-radius: var(--md-radius-lg); background-color: var(--md-secondary-container);">
              <p class="md-title-small font-semibold" style="color: var(--md-on-secondary-container);">🏆 最佳选择：版本 {{ parsedEvaluation.best_choice }}</p>
              <p class="md-body-small mt-2" style="color: var(--md-on-secondary-container);">{{ parsedEvaluation.reason_for_choice }}</p>
            </div>
            <div class="space-y-4">
              <div v-for="(evalResult, versionName) in parsedEvaluation.evaluation" :key="versionName" class="md-card md-card-outlined p-4" style="border-radius: var(--md-radius-lg);">
                <h5 class="md-title-medium font-semibold mb-2">版本 {{ String(versionName).replace('version', '') }} 评估</h5>
                <div class="prose prose-sm max-w-none md-on-surface space-y-3">
                  <div>
                    <p class="font-semibold">综合评价:</p>
                    <p>{{ evalResult.overall_review }}</p>
                  </div>
                  <div>
                    <p class="font-semibold">优点:</p>
                    <ul class="list-disc pl-5 space-y-1">
                      <li v-for="(pro, i) in evalResult.pros" :key="`pro-${i}`">{{ pro }}</li>
                    </ul>
                  </div>
                  <div>
                    <p class="font-semibold">缺点:</p>
                    <ul class="list-disc pl-5 space-y-1">
                      <li v-for="(con, i) in evalResult.cons" :key="`con-${i}`">{{ con }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div 
            v-else
            class="prose prose-sm max-w-none prose-headings:mt-2 prose-headings:mb-1 prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0"
            style="color: var(--md-on-surface);"
            v-html="parseMarkdown(evaluation)"
          ></div>
      </div>

      <!-- 弹窗底部操作按钮 -->
      <div class="flex items-center justify-end p-6 border-t" style="border-top-color: var(--md-outline-variant); background-color: var(--md-surface-container-low);">
        <button
            @click="$emit('close')"
            class="md-btn md-btn-filled md-ripple"
        >
            关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  show: boolean
  evaluation: string | null
}

const props = defineProps<Props>()

defineEmits(['close'])

const parsedEvaluation = computed(() => {
  if (!props.evaluation) return null
  try {
    let rawData = props.evaluation

    // 移除 markdown 代码块包装 (```json ... ``` 或 ``` ... ```)
    const codeBlockMatch = rawData.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (codeBlockMatch) {
      rawData = codeBlockMatch[1].trim()
    }

    // 尝试解析 JSON
    let data = JSON.parse(rawData)

    // 如果解析结果是字符串，可能是双重编码，再解析一次
    if (typeof data === 'string') {
      data = JSON.parse(data)
    }

    return data
  } catch (error) {
    console.error('Failed to parse evaluation JSON:', error)
    return null
  }
})

const parseMarkdown = (text: string | null): string => {
  if (!text) return ''
  let parsed = text

  // 移除 markdown 代码块标记，但保留内容
  parsed = parsed.replace(/```(?:json|javascript|typescript|js|ts)?\s*/g, '')
  parsed = parsed.replace(/```/g, '')

  // 处理转义字符
  parsed = parsed
    .replace(/\\n/g, '\n')
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\\\/g, '\\')

  // 尝试格式化 JSON 内容使其更易读
  try {
    const jsonData = JSON.parse(parsed)
    // 如果解析成功，返回格式化的 HTML
    return formatJsonToHtml(jsonData)
  } catch {
    // 如果不是 JSON，继续用 markdown 解析
  }

  parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  parsed = parsed.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
  parsed = parsed.replace(
    /^([A-Z])\)\s*\*\*(.*?)\*\*(.*)/gm,
    '<div class="mb-2"><span class="inline-flex items-center justify-center w-6 h-6 text-sm font-bold rounded-full mr-2" style="background-color: var(--md-primary-container); color: var(--md-on-primary-container);">$1</span><strong>$2</strong>$3</div>'
  )
  parsed = parsed.replace(/\n/g, '<br>')
  parsed = parsed.replace(/(<br\s*\/?>\s*){2,}/g, '</p><p class="mt-2">')
  if (!parsed.includes('<p>')) {
    parsed = `<p>${parsed}</p>`
  }
  return parsed
}

// 将 JSON 对象格式化为可读的 HTML
const formatJsonToHtml = (data: any): string => {
  if (!data) return ''

  const sections: string[] = []

  // 最佳选择
  if (data.best_choice !== undefined) {
    sections.push(`
      <div class="mb-4 p-4 rounded-lg" style="background-color: var(--md-secondary-container);">
        <p class="font-semibold" style="color: var(--md-on-secondary-container);">🏆 最佳选择：版本 ${data.best_choice}</p>
        ${data.reason_for_choice ? `<p class="mt-2 text-sm" style="color: var(--md-on-secondary-container);">${data.reason_for_choice}</p>` : ''}
      </div>
    `)
  }

  // 整体评价
  if (data.overall_review) {
    sections.push(`
      <div class="mb-4">
        <p class="font-semibold mb-2">📝 整体评价</p>
        <p class="text-sm">${data.overall_review}</p>
      </div>
    `)
  }

  // 各版本评估
  if (data.evaluation) {
    for (const [versionName, evalResult] of Object.entries(data.evaluation)) {
      const result = evalResult as any
      const versionNum = String(versionName).replace('version', '')
      let versionHtml = `
        <div class="mb-4 p-4 border rounded-lg" style="border-color: var(--md-outline-variant);">
          <h5 class="font-semibold mb-3">版本 ${versionNum} 评估</h5>
      `

      if (result.overall_review) {
        versionHtml += `<div class="mb-3"><p class="font-medium text-sm">综合评价:</p><p class="text-sm">${result.overall_review}</p></div>`
      }

      if (result.pros && result.pros.length) {
        versionHtml += `
          <div class="mb-3">
            <p class="font-medium text-sm text-green-600">✅ 优点:</p>
            <ul class="list-disc pl-5 text-sm space-y-1">
              ${result.pros.map((pro: string) => `<li>${pro}</li>`).join('')}
            </ul>
          </div>
        `
      }

      if (result.cons && result.cons.length) {
        versionHtml += `
          <div class="mb-3">
            <p class="font-medium text-sm text-red-600">❌ 缺点:</p>
            <ul class="list-disc pl-5 text-sm space-y-1">
              ${result.cons.map((con: string) => `<li>${con}</li>`).join('')}
            </ul>
          </div>
        `
      }

      versionHtml += '</div>'
      sections.push(versionHtml)
    }
  }

  return sections.join('') || `<pre class="text-xs overflow-auto p-3 rounded-lg" style="background-color: var(--md-surface-container);">${JSON.stringify(data, null, 2)}</pre>`
}
</script>

<style scoped>
.m3-eval-dialog {
  max-width: min(960px, calc(100vw - 32px));
  max-height: calc(100vh - 32px);
  border-radius: var(--md-radius-xl);
}
</style>
