<script setup lang="ts">
import { useSessionStore } from '../../stores/session'
import { ref, watch, nextTick } from 'vue'
import { sessionsApi } from '../../api'
import MessageItem from './MessageItem.vue'
import type { AgentEvent } from '../../composables/useWebSocket'

interface Message {
  role: string
  content: string | null
  tool_calls?: any[]
  tool_call_id?: string
  isStreaming?: boolean
}

const store = useSessionStore()
const messages = ref<Message[]>([])
const listRef = ref<HTMLElement>()
const isThinking = ref(false)
const streamingToolCalls = ref<Map<string, { tool: string; args: string; result?: string; duration_ms?: number }>>(new Map())

async function loadMessages(sessionId: string) {
  try {
    const res = await sessionsApi.get(sessionId) as any
    messages.value = res.messages || []
  } catch {
    messages.value = []
  }
  isThinking.value = false
  streamingToolCalls.value = new Map()
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight
  }
}

/** 处理 WebSocket 实时事件 */
function handleEvent(event: AgentEvent) {
  switch (event.type) {
    case 'thinking':
      isThinking.value = true
      break
    case 'tool_call':
      isThinking.value = false
      streamingToolCalls.value.set(event.tool_call_id || Math.random().toString(), {
        tool: event.tool || '',
        args: event.args || '',
      })
      break
    case 'tool_result':
      if (event.tool_call_id) {
        const tc = streamingToolCalls.value.get(event.tool_call_id)
        if (tc) {
          tc.result = event.result
          tc.duration_ms = event.duration_ms
        }
      }
      break
    case 'done':
      isThinking.value = false
      streamingToolCalls.value.clear()
      if (store.currentId) loadMessages(store.currentId)
      return
    case 'error':
      isThinking.value = false
      streamingToolCalls.value.clear()
      return
  }
  nextTick(scrollToBottom)
}

watch(() => store.currentId, (id) => {
  if (id) loadMessages(id)
  else {
    messages.value = []
    isThinking.value = false
    streamingToolCalls.value = new Map()
  }
})

defineExpose({ messages, scrollToBottom, loadMessages, handleEvent })
</script>

<template>
  <div ref="listRef" class="message-list">
    <div v-if="!store.currentId" class="empty">
      选择或创建一个会话开始
    </div>
    <template v-else>
      <!-- 历史消息 -->
      <MessageItem
        v-for="(msg, i) in messages"
        :key="'h'+i"
        :message="msg"
      />
      <!-- 实时工具调用 -->
      <div v-if="streamingToolCalls.size" class="streaming-events">
        <div class="streaming-label">正在执行 ({{ streamingToolCalls.size }} 个任务并行)...</div>
        <div v-for="[id, tc] in streamingToolCalls" :key="id" class="streaming-tool">
          <div class="tool-header">
            <span class="tool-badge">{{ tc.tool }}</span>
            <span v-if="tc.duration_ms" class="tool-duration">{{ tc.duration_ms }}ms</span>
            <span v-else class="tool-running">运行中...</span>
          </div>
          <details v-if="tc.args" class="tool-details">
            <summary>参数</summary>
            <code>{{ tc.args }}</code>
          </details>
        </div>
      </div>
      <!-- 思考中指示器 -->
      <div v-if="isThinking" class="thinking-indicator">
        <span class="thinking-dot"></span>
        <span class="thinking-dot"></span>
        <span class="thinking-dot"></span>
        <span class="thinking-text">思考中...</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
}
.streaming-events {
  padding: 12px;
  margin: 8px 0;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.streaming-label {
  font-size: 12px;
  color: var(--primary);
  margin-bottom: 8px;
  font-weight: 500;
}
.streaming-tool {
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}
.streaming-tool:last-child {
  border-bottom: none;
}
.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tool-badge {
  background: var(--primary);
  color: white;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.tool-duration {
  font-size: 11px;
  color: var(--success);
}
.tool-running {
  font-size: 11px;
  color: var(--text-muted);
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.tool-details {
  margin-top: 4px;
}
.tool-details summary {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 12px;
}
.tool-details code {
  display: block;
  padding: 6px;
  margin-top: 4px;
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  font-size: 11px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 0;
  margin-left: 52px;
}
.thinking-dot {
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.thinking-dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
.thinking-text {
  margin-left: 6px;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
