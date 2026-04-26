<script setup lang="ts">
import { computed } from 'vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import ToolCallBlock from './ToolCallBlock.vue'

const props = defineProps<{ message: any }>()

const isUser = computed(() => props.message.role === 'user')
const isSystem = computed(() => props.message.role === 'system')
const isTool = computed(() => props.message.role === 'tool')
const hasToolCalls = computed(() => props.message.tool_calls?.length > 0)
const showContent = computed(() => props.message.content && !isTool.value && !isSystem.value)
</script>

<template>
  <div class="message" :class="[message.role]">
    <div class="role-label">
      {{ isUser ? '你' : isTool ? '工具' : isSystem ? '系统' : '助手' }}
    </div>
    <div class="message-body">
      <!-- 工具调用块 -->
      <ToolCallBlock
        v-if="hasToolCalls"
        :tool-calls="message.tool_calls"
      />
      <!-- 工具返回（折叠） -->
      <div v-if="isTool" class="tool-result">
        <details>
          <summary>工具返回结果</summary>
          <div class="tool-result-content">{{ message.content }}</div>
        </details>
      </div>
      <!-- 文本内容 -->
      <MarkdownRenderer v-if="showContent" :content="message.content" />
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}
.message:last-child {
  border-bottom: none;
}
.role-label {
  width: 40px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  padding-top: 2px;
}
.message.user .role-label {
  color: var(--primary);
}
.message.assistant .role-label {
  color: var(--success);
}
.message-body {
  flex: 1;
  min-width: 0;
}
.tool-result {
  font-size: 13px;
  color: var(--text-secondary);
}
.tool-result summary {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 12px;
  padding: 4px 0;
}
.tool-result-content {
  background: var(--bg-hover);
  padding: 8px;
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
</style>
