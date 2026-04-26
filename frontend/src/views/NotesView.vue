<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notesApi } from '../api'
import NoteCard from '../components/notes/NoteCard.vue'
import NotePreview from '../components/notes/NotePreview.vue'

interface Note {
  id: number
  session_id: string | null
  title: string
  summary: string
  created_at: string
  updated_at: string
}

const notes = ref<Note[]>([])
const selectedNote = ref<any>(null)
const loading = ref(false)

async function fetchNotes() {
  const data = await notesApi.list() as any
  notes.value = data
}

async function selectNote(id: number) {
  loading.value = true
  try {
    selectedNote.value = await notesApi.get(id)
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: number) {
  await notesApi.delete(id)
  if (selectedNote.value?.id === id) selectedNote.value = null
  await fetchNotes()
}

onMounted(fetchNotes)
</script>

<template>
  <div class="notes-layout">
    <div class="notes-list-panel">
      <h3 class="panel-title">笔记列表</h3>
      <div class="note-cards">
        <NoteCard
          v-for="note in notes"
          :key="note.id"
          :note="note"
          :active="selectedNote?.id === note.id"
          @click="selectNote(note.id)"
          @delete="handleDelete(note.id)"
        />
        <div v-if="!notes.length" class="empty">暂无笔记</div>
      </div>
    </div>
    <div class="notes-preview-panel">
      <NotePreview v-if="selectedNote" :note="selectedNote" />
      <div v-else class="empty">选择左侧笔记查看</div>
    </div>
  </div>
</template>

<style scoped>
.notes-layout {
  display: flex;
  height: calc(100vh - 48px);
}
.notes-list-panel {
  width: 320px;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 16px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-secondary);
}
.note-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.notes-preview-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
.empty {
  color: var(--text-muted);
  text-align: center;
  padding: 48px 16px;
  font-size: 14px;
}
</style>
