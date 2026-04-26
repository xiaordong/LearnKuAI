<script setup lang="ts">
defineProps<{
  note: {
    id: number
    title: string
    summary: string
    updated_at: string
  }
  active: boolean
}>()

const emit = defineEmits<{
  delete: []
}>()
</script>

<template>
  <div class="note-card" :class="{ active }">
    <div class="note-title">{{ note.title }}</div>
    <div class="note-summary">{{ note.summary }}</div>
    <div class="note-footer">
      <span class="note-time">{{ note.updated_at?.slice(0, 16) }}</span>
      <button class="delete-btn" @click.stop="emit('delete')" title="删除">删除</button>
    </div>
  </div>
</template>

<style scoped>
.note-card {
  padding: 10px 12px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.15s;
}
.note-card:hover {
  background: var(--bg-hover);
}
.note-card.active {
  border-color: var(--primary);
  background: var(--bg-hover);
}
.note-title {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.note-summary {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.note-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 6px;
}
.note-time {
  font-size: 11px;
  color: var(--text-muted);
}
.delete-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}
.delete-btn:hover {
  color: var(--error);
  background: rgba(239, 68, 68, 0.1);
}
</style>
