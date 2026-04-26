<script setup lang="ts">
import { NMenu, type MenuOption } from 'naive-ui'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const menuOptions: MenuOption[] = [
  { label: '对话', key: 'chat' },
  { label: '日志', key: 'logs' },
  { label: '笔记', key: 'notes' },
]

function handleMenuClick(key: string) {
  const pathMap: Record<string, string> = { chat: '/', logs: '/logs', notes: '/notes' }
  router.push(pathMap[key] || '/')
}

function currentKey(): string {
  const map: Record<string, string> = { '/': 'chat', '/logs': 'logs', '/notes': 'notes' }
  return map[route.path] || 'chat'
}
</script>

<template>
  <div class="top-nav">
    <div class="logo" @click="router.push('/')">LearnKuAI</div>
    <NMenu
      mode="horizontal"
      :value="currentKey()"
      :options="menuOptions"
      @update:value="handleMenuClick"
    />
  </div>
</template>

<style scoped>
.top-nav {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
}
.logo {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  margin-right: 24px;
  cursor: pointer;
  user-select: none;
}
</style>
