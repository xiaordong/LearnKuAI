<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logsApi } from '../api'
import MetricsCards from '../components/logs/MetricsCards.vue'
import ToolUsageChart from '../components/logs/ToolUsageChart.vue'
import TimelineChart from '../components/logs/TimelineChart.vue'

const stats = ref({ api_calls: 0, tool_calls: 0, avg_duration_ms: 0, error_rate: 0, total_logs: 0 })
const toolUsage = ref<{ tool_name: string; count: number }[]>([])
const timeline = ref<{ hour: string; total: number; errors: number }[]>([])

onMounted(async () => {
  const [s, t, tl] = await Promise.all([
    logsApi.stats(),
    logsApi.tools(),
    logsApi.timeline(),
  ])
  stats.value = s as any
  toolUsage.value = t as any
  timeline.value = tl as any
})
</script>

<template>
  <div class="logs-page">
    <MetricsCards :stats="stats" />
    <div class="charts-row">
      <ToolUsageChart :data="toolUsage" />
      <TimelineChart :data="timeline" />
    </div>
  </div>
</template>

<style scoped>
.logs-page {
  height: calc(100vh - 48px);
  overflow-y: auto;
  padding: 24px;
}
.charts-row {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}
.charts-row > * {
  flex: 1;
  min-width: 0;
}
</style>
