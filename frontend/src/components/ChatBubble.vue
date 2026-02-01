<!-- AIMETA P=聊天气泡_对话消息展示|R=消息气泡|NR=不含输入功能|E=component:ChatBubble|X=internal|A=气泡组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div :class="wrapperClass">
    <div :class="bubbleClass">
      <!-- AI message - Parchment/Scroll style -->
      <div v-if="type === 'ai'" class="ai-bubble-content">
        <!-- Scroll decoration -->
        <div class="scroll-decoration scroll-top"></div>

        <!-- Avatar -->
        <div class="ai-avatar">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.707 5.293a1 1 0 010 1.414l-1.414 1.414a1 1 0 01-1.414 0L14 4.243 4.929 13.314a2 2 0 00-.499.838l-1.414 4.243a1 1 0 001.213 1.213l4.243-1.414a2 2 0 00.838-.499l9.071-9.071-3.879-3.879-1.414 1.414a1 1 0 11-1.414-1.414L13.414 3l1.293-1.293a1 1 0 011.414 0l4.586 4.586z" />
          </svg>
        </div>

        <!-- Message content -->
        <div
          class="prose prose-sm max-w-none prose-headings:mt-2 prose-headings:mb-1 prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 ai-message-text"
          v-html="renderedMessage"
        ></div>

        <div class="scroll-decoration scroll-bottom"></div>
      </div>

      <!-- User message - Envelope/Note style -->
      <div v-else class="user-bubble-content">
        <!-- Wax seal decoration -->
        <div class="seal-decoration">
          <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <div class="user-message-text">{{ message }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  message: string
  type: 'user' | 'ai'
}

const props = defineProps<Props>()

// Simple markdown parser
const parseMarkdown = (text: string): string => {
  if (!text) return ''

  // Handle escape characters
  let parsed = text
    .replace(/\\n/g, '\n')
    .replace(/\\\"/g, '"')
    .replace(/\\'/g, "'")
    .replace(/\\\\/g, '\\')

  // Handle bold text **text**
  parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // Handle italic text *text*
  parsed = parsed.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')

  // Handle option lists A) text - now with novel theme colors
  parsed = parsed.replace(
    /^([A-Z])\)\s*\*\*(.*?)\*\*(.*)/gm,
    '<div class="option-item"><span class="option-label">$1</span><strong>$2</strong>$3</div>'
  )

  // Handle line breaks
  parsed = parsed.replace(/\n/g, '<br>')

  // Handle multiple <br> tags as paragraphs
  parsed = parsed.replace(/(<br\s*\/?>\s*){2,}/g, '</p><p class="mt-2">')

  // Wrap in paragraph tags
  if (!parsed.includes('<p>')) {
    parsed = `<p>${parsed}</p>`
  }

  return parsed
}

const renderedMessage = computed(() => {
  if (props.type === 'ai') {
    return parseMarkdown(props.message)
  }
  return props.message
})

const wrapperClass = computed(() => {
  return `chat-bubble-wrapper ${props.type === 'ai' ? 'bubble-left' : 'bubble-right'}`
})

const bubbleClass = computed(() => {
  return `chat-bubble ${props.type === 'ai' ? 'chat-bubble-ai' : 'chat-bubble-user'}`
})
</script>

<style scoped>
/* Wrapper */
.chat-bubble-wrapper {
  width: 100%;
  display: flex;
  animation: bubble-appear 0.3s var(--novel-easing-emphasized);
}

@keyframes bubble-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bubble-left {
  justify-content: flex-start;
}

.bubble-right {
  justify-content: flex-end;
}

/* Chat bubble base */
.chat-bubble {
  max-width: 85%;
  position: relative;
}

@media (min-width: 768px) {
  .chat-bubble {
    max-width: 70%;
  }
}

/* AI Bubble - Parchment/Scroll style */
.chat-bubble-ai {
  background: var(--novel-parchment);
  border: 1px solid var(--novel-outline-variant);
  border-radius: var(--novel-radius-lg) var(--novel-radius-lg) var(--novel-radius-lg) var(--novel-radius-sm);
  box-shadow: var(--novel-shadow-md);
  position: relative;
  overflow: hidden;
}

.chat-bubble-ai::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  opacity: 0.5;
  pointer-events: none;
}

.ai-bubble-content {
  padding: var(--novel-space-4);
  position: relative;
}

/* Scroll decorations */
.scroll-decoration {
  position: absolute;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--novel-outline-variant) 20%,
    var(--novel-outline-variant) 80%,
    transparent 100%
  );
  opacity: 0.5;
}

.scroll-top {
  top: 0;
}

.scroll-bottom {
  bottom: 0;
}

/* AI Avatar */
.ai-avatar {
  position: absolute;
  top: var(--novel-space-3);
  left: calc(-1 * var(--novel-space-10));
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
  display: none;
  align-items: center;
  justify-content: center;
  box-shadow: var(--novel-shadow-sm);
}

@media (min-width: 1024px) {
  .ai-avatar {
    display: flex;
  }

  .ai-bubble-content {
    margin-left: var(--novel-space-2);
  }
}

.ai-message-text {
  color: var(--novel-on-surface);
  line-height: 1.6;
}

/* Option items styling */
.ai-message-text :deep(.option-item) {
  display: flex;
  align-items: flex-start;
  gap: var(--novel-space-2);
  margin-bottom: var(--novel-space-2);
  padding: var(--novel-space-2) var(--novel-space-3);
  background: var(--novel-surface);
  border-radius: var(--novel-radius-md);
  border: 1px solid var(--novel-outline-variant);
}

.ai-message-text :deep(.option-label) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  min-width: 24px;
  background: var(--novel-primary-container);
  color: var(--novel-on-primary-container);
  font-size: var(--novel-text-caption);
  font-weight: 600;
  border-radius: 50%;
}

/* User Bubble - Envelope/Note style */
.chat-bubble-user {
  background: var(--novel-primary);
  color: var(--novel-on-primary);
  border-radius: var(--novel-radius-lg) var(--novel-radius-lg) var(--novel-radius-sm) var(--novel-radius-lg);
  box-shadow: var(--novel-shadow-md);
  position: relative;
}

.chat-bubble-user::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: -6px;
  width: 12px;
  height: 12px;
  background: inherit;
  clip-path: polygon(0 0, 100% 0, 100% 100%);
  display: none;
}

.user-bubble-content {
  padding: var(--novel-space-3) var(--novel-space-4);
  position: relative;
}

/* Wax seal decoration */
.seal-decoration {
  position: absolute;
  top: calc(-1 * var(--novel-space-2));
  right: var(--novel-space-3);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--novel-error);
  color: var(--novel-on-error);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--novel-shadow-sm);
  opacity: 0;
  transition: opacity var(--novel-duration-fast);
}

.chat-bubble-user:hover .seal-decoration {
  opacity: 0.8;
}

.user-message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

/* Prose overrides for dark mode */
:root[data-theme="dark"] .ai-message-text :deep(.option-item) {
  background: var(--novel-surface-container);
}

:root[data-theme="dark"] .chat-bubble-ai {
  background: var(--novel-surface-container);
}

:root[data-theme="dark"] .chat-bubble-ai::before {
  opacity: 0.3;
}
</style>
