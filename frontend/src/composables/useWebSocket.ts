/** WebSocket 连接管理 */
import { ref } from 'vue'

export interface AgentEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'done' | 'error'
  tool_call_id?: string
  tool?: string
  args?: string
  result?: string
  duration_ms?: number
  content?: string
  message?: string
}

export function useWebSocket(getWsUrl: () => string) {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const events = ref<AgentEvent[]>([])
  const running = ref(false)
  const errorMsg = ref('')
  let onEventCb: ((event: AgentEvent) => void) | null = null

  function connect() {
    disconnect()
    const url = getWsUrl()
    if (!url) return

    console.log('[WS] 连接:', url)
    const socket = new WebSocket(url)

    socket.onopen = () => {
      console.log('[WS] 已连接')
      connected.value = true
      errorMsg.value = ''
    }

    socket.onclose = (e) => {
      console.log('[WS] 断开:', e.code, e.reason)
      connected.value = false
    }

    socket.onerror = () => {
      console.error('[WS] 连接失败')
      connected.value = false
      errorMsg.value = 'WebSocket 连接失败'
    }

    socket.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data)
        console.log('[WS] 事件:', event.type, event.tool || event.content?.slice(0, 50) || '')
        events.value.push(event)
        if (event.type === 'done' || event.type === 'error') {
          running.value = false
        }
        onEventCb?.(event)
      } catch (err) {
        console.error('[WS] 解析失败:', err)
      }
    }

    ws.value = socket
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
  }

  function send(content: string) {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.warn('[WS] 未连接，尝试重连...')
      errorMsg.value = '未连接，正在重连...'
      connect()
      const doSend = () => {
        if (ws.value && ws.value.readyState === WebSocket.OPEN) {
          running.value = true
          events.value = []
          errorMsg.value = ''
          ws.value.send(JSON.stringify({ type: 'message', content }))
          console.log('[WS] 已发送:', content.slice(0, 50))
        }
      }
      ws.value?.addEventListener('open', doSend, { once: true })
      // 5 秒超时：连不上就放弃
      setTimeout(() => {
        if (!connected.value) {
          errorMsg.value = '连接超时，请检查后端'
          running.value = false
        }
      }, 5000)
      return
    }
    running.value = true
    events.value = []
    errorMsg.value = ''
    ws.value.send(JSON.stringify({ type: 'message', content }))
    console.log('[WS] 已发送:', content.slice(0, 50))
  }

  function cancel() {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) return
    ws.value.send(JSON.stringify({ type: 'cancel' }))
    running.value = false
  }

  function onEvent(cb: (event: AgentEvent) => void) {
    onEventCb = cb
  }

  return { ws, connected, events, running, errorMsg, connect, disconnect, send, cancel, onEvent }
}
