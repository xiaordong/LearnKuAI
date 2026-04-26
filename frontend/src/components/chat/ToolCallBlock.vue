<script setup lang="ts">
const props = defineProps<{ toolCalls: any[] }>()

function parseArgs(args: string | undefined): string {
  if (!args) return '{}'
  try {
    return JSON.stringify(JSON.parse(args), null, 2)
  } catch {
    return args
  }
}

function toolDisplayName(name: string): string {
  const map: Record<string, string> = {
    search: '搜索',
    fetch_page: '抓取网页',
    save_note: '保存笔记',
    read_note: '读取笔记',
    list_notes: '列出笔记',
    get_current_time: '获取时间',
    update_plan: '更新计划',
    read_plan: '读取计划',
  }
  return map[name] || name
}
</script>

<template>
  <div class="tool-calls">
    <details v-for="(tc, i) in toolCalls" :key="i" class="tool-call-item" open>
      <summary class="tool-call-header">
        <span class="tool-badge">{{ toolDisplayName(tc.function.name) }}</span>
        <span class="tool-name">{{ tc.function.name }}</span>
      </summary>
      <div class="tool-args">
        <code>{{ parseArgs(tc.function.arguments) }}</code>
      </div>
    </details>
  </div>
</template>

<style scoped>
.tool-calls {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
.tool-call-item {
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 13px;
}
.tool-call-header:hover {
  background: var(--bg-input);
}
.tool-badge {
  background: var(--primary);
  color: white;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.tool-name {
  color: var(--text-muted);
  font-size: 12px;
}
.tool-args {
  padding: 8px 10px;
  border-top: 1px solid var(--border);
}
.tool-args code {
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
