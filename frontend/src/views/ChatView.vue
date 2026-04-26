<script setup lang="ts">
import { useSessionStore } from '../stores/session'
import SessionSidebar from '../components/chat/SessionSidebar.vue'
import MessageList from '../components/chat/MessageList.vue'
import InputBar from '../components/chat/InputBar.vue'
import { useWebSocket, type AgentEvent } from '../composables/useWebSocket'
import { ref, watch, onUnmounted, nextTick } from 'vue'

const store = useSessionStore()
const messageListRef = ref<InstanceType<typeof MessageList>>()

function wsUrl() {
  if (!store.currentId) return ''
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${location.host}/ws/agent/${store.currentId}`
}

const { connected, running, errorMsg, connect, disconnect, send, cancel, onEvent } = useWebSocket(wsUrl)

function handleCancel() {
  cancel()
  // 立即清除 MessageList 的思考/工具调用状态
  messageListRef.value?.handleEvent({ type: 'error', message: '已取消' })
}

// 会话切换时重连 WebSocket
watch(() => store.currentId, async (id) => {
  if (id) {
    disconnect()
    await nextTick()
    connect()
  } else {
    disconnect()
  }
}, { immediate: true })

onUnmounted(disconnect)

// 将 WebSocket 事件转发给 MessageList 实时展示
onEvent((event: AgentEvent) => {
  messageListRef.value?.handleEvent(event)
  // agent 完成后刷新侧栏标题
  if (event.type === 'done' || event.type === 'error') {
    store.fetchSessions()
  }
})

store.fetchSessions()
</script>

<template>
  <div class="chat-layout">
    <SessionSidebar />
    <div class="chat-main">
      <!-- 连接状态栏 -->
      <div v-if="store.currentId && !connected && !running" class="status-bar warn">
        {{ errorMsg || 'WebSocket 未连接，请检查后端是否运行' }}
      </div>
      <MessageList ref="messageListRef" />
      <InputBar :running="running" @send="send" @cancel="handleCancel" />
    </div>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 48px);
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.status-bar {
  padding: 6px 16px;
  font-size: 12px;
  text-align: center;
}
.status-bar.warn {
  background: rgba(234, 179, 8, 0.1);
  color: var(--warning);
  border-bottom: 1px solid var(--border);
}
</style>
