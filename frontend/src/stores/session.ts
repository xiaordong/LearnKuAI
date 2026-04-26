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

  async function fetchSessions() {
    const data = await sessionsApi.list() as any
    sessions.value = data
  }

  async function createSession() {
    const res = await sessionsApi.create() as any
    currentId.value = res.id
    await fetchSessions()
    return res.id
  }

  async function deleteSession(id: string) {
    await sessionsApi.delete(id)
    if (currentId.value === id) currentId.value = null
    await fetchSessions()
  }

  return { sessions, currentId, fetchSessions, createSession, deleteSession }
})
