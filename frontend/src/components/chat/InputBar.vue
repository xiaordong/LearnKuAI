<script setup lang="ts">
import { ref, nextTick } from 'vue'

const props = defineProps<{ running: boolean }>()
const emit = defineEmits<{
  send: [content: string]
  cancel: []
}>()

const input = ref('')
const textareaRef = ref<HTMLTextAreaElement>()

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function handleSend() {
  const text = input.value.trim()
  if (!text) return
  emit('send', text)
  input.value = ''
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="input-bar">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="input"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        rows="1"
        @keydown="handleKeydown"
        @input="autoResize"
        :disabled="running"
      />
      <button v-if="!running" class="send-btn" @click="handleSend" :disabled="!input.trim()">
        发送
      </button>
      <button v-else class="cancel-btn" @click="emit('cancel')">
        取消
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-bar {
  border-top: 1px solid var(--border);
  padding: 12px 16px;
  background: var(--bg-card);
}
.input-wrapper {
  display: flex;
  gap: 8px;
  max-width: 800px;
  margin: 0 auto;
}
textarea {
  flex: 1;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  padding: 10px 14px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  min-height: 40px;
  max-height: 120px;
}
textarea:focus {
  border-color: var(--primary);
}
textarea:disabled {
  opacity: 0.5;
}
.send-btn {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  padding: 0 20px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}
.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}
.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.cancel-btn {
  background: var(--error);
  color: white;
  border: none;
  border-radius: var(--radius);
  padding: 0 20px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}
</style>
