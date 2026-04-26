<script setup lang="ts">
import MarkdownRenderer from '../chat/MarkdownRenderer.vue'
import { notesApi } from '../../api'

const props = defineProps<{
  note: {
    id: number
    title: string
    content: string
  }
}>()
</script>

<template>
  <div class="note-preview">
    <div class="preview-header">
      <h2>{{ note.title }}</h2>
      <a :href="notesApi.download(note.id)" download class="download-btn">下载</a>
    </div>
    <MarkdownRenderer :content="note.content" />
  </div>
</template>

<style scoped>
.note-preview {
  max-width: 800px;
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.preview-header h2 {
  font-size: 20px;
  font-weight: 600;
}
.download-btn {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: var(--radius);
  text-decoration: none;
  font-size: 13px;
}
.download-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}
</style>
