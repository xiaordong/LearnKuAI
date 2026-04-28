import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sessionsApi } from '../api'

export interface Session {
  id: string
  title: string
  updated_at: string
}

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentId = ref<string | null>(null)
  const error = ref('')

  async function fetchSessions() {
    try {
      error.value = ''
      const data = await sessionsApi.list() as any
      sessions.value = data
    } catch (e: any) {
      error.value = `加载会话列表失败: ${e.message || e}`
      console.error('[SessionStore] fetchSessions 失败:', e)
    }
  }

  async function createSession() {
    try {
      error.value = ''
      const res = await sessionsApi.create() as any
      currentId.value = res.id
      await fetchSessions()
      return res.id
    } catch (e: any) {
      error.value = `创建会话失败: ${e.message || e}`
      console.error('[SessionStore] createSession 失败:', e)
    }
  }

  async function deleteSession(id: string) {
    try {
      error.value = ''
      await sessionsApi.delete(id)
      if (currentId.value === id) currentId.value = null
      await fetchSessions()
    } catch (e: any) {
      error.value = `删除会话失败: ${e.message || e}`
      console.error('[SessionStore] deleteSession 失败:', e)
    }
  }

  function clearError() {
    error.value = ''
  }

  return { sessions, currentId, error, fetchSessions, createSession, deleteSession, clearError }
})
