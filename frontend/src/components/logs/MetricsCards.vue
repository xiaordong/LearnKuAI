<script setup lang="ts">
const props = defineProps<{
  stats: {
    api_calls: number
    tool_calls: number
    avg_duration_ms: number
    error_rate: number
    total_logs: number
  }
}>()

const cards = computed(() => [
  { label: 'API 调用', value: props.stats.api_calls, color: '#3b82f6' },
  { label: '工具调用', value: props.stats.tool_calls, color: '#22c55e' },
  { label: '平均耗时', value: `${props.stats.avg_duration_ms}ms`, color: '#eab308' },
  { label: '错误率', value: `${props.stats.error_rate}%`, color: '#ef4444' },
])

import { computed } from 'vue'
</script>

<template>
  <div class="metrics">
    <div v-for="card in cards" :key="card.label" class="metric-card">
      <div class="metric-value" :style="{ color: card.color }">{{ card.value }}</div>
      <div class="metric-label">{{ card.label }}</div>
    </div>
  </div>
</template>

<style scoped>
.metrics {
  display: flex;
  gap: 16px;
}
.metric-card {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  text-align: center;
}
.metric-value {
  font-size: 28px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.metric-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
