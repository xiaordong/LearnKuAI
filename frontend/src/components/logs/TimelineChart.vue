<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const props = defineProps<{ data: { hour: string; total: number; errors: number }[] }>()

const option = computed(() => ({
  backgroundColor: 'transparent',
  title: {
    text: '活动时间线',
    textStyle: { color: '#e5e5e5', fontSize: 14 },
    left: 'center',
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#1a1a1a',
    borderColor: '#333',
    textStyle: { color: '#e5e5e5' },
  },
  grid: { left: 50, right: 20, top: 50, bottom: 30 },
  xAxis: {
    type: 'category',
    data: props.data.map(d => d.hour?.slice(5) || ''),
    axisLine: { lineStyle: { color: '#333' } },
    axisLabel: { color: '#737373', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: '#333' } },
    axisLabel: { color: '#737373' },
    splitLine: { lineStyle: { color: '#1a1a1a' } },
  },
  series: [
    {
      name: '总日志',
      type: 'line',
      data: props.data.map(d => d.total),
      smooth: true,
      lineStyle: { color: '#3b82f6' },
      itemStyle: { color: '#3b82f6' },
      areaStyle: { color: 'rgba(59,130,246,0.1)' },
    },
    {
      name: '错误',
      type: 'line',
      data: props.data.map(d => d.errors),
      smooth: true,
      lineStyle: { color: '#ef4444' },
      itemStyle: { color: '#ef4444' },
    },
  ],
}))
</script>

<template>
  <div class="chart-card">
    <VChart :option="option" autoresize style="height: 320px" />
  </div>
</template>

<style scoped>
.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
</style>
