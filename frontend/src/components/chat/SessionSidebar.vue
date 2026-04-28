<script setup lang="ts">
import { useSessionStore } from '../../stores/session'
import { NButton, NSpin } from 'naive-ui'

const store = useSessionStore()

function handleDelete(id: string, title: string) {
  if (!window.confirm(`确定删除会话「${title || '无标题'}」吗？此操作不可撤销。`)) return
  store.deleteSession(id)
}
</script>

<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">会话</span>
      <NButton size="small" quaternary @click="store.createSession()">新建</NButton>
    </div>
    <!-- 错误提示 -->
    <div v-if="store.error" class="error-bar">
      {{ store.error }}
      <button class="dismiss-btn" @click="store.clearError()">×</button>
    </div>
    <div class="session-list">
      <NSpin v-if="!store.sessions.length" size="small" />
      <div
        v-for="s in store.sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: store.currentId === s.id }"
        @click="store.currentId = s.id"
      >
        <div class="session-title">{{ s.title || '无标题' }}</div>
        <div class="session-time">{{ s.updated_at?.slice(5, 16) }}</div>
        <button class="delete-btn" @click.stop="handleDelete(s.id, s.title)" title="删除">×</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 260px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border);
}
.sidebar-title {
  font-size: 14px;
  font-weight: 600;
}
.error-bar {
  padding: 8px 12px;
  font-size: 12px;
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dismiss-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.session-item {
  padding: 8px 12px;
  border-radius: var(--radius);
  cursor: pointer;
  margin-bottom: 2px;
  position: relative;
  transition: background 0.15s;
}
.session-item:hover {
  background: var(--bg-hover);
}
.session-item.active {
  background: var(--bg-hover);
  border-left: 2px solid var(--primary);
}
.session-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 20px;
}
.session-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}
.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  display: none;
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  border-radius: var(--radius-sm);
}
.session-item:hover .delete-btn {
  display: block;
}
.delete-btn:hover {
  background: var(--bg-input);
  color: var(--error);
}
</style>
