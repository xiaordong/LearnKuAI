<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{ data: { tool_name: string; count: number }[] }>()

const colors = ['#3b82f6', '#22c55e', '#eab308', '#ef4444', '#a855f7', '#06b6d4', '#f97316']

const option = computed(() => ({
  backgroundColor: 'transparent',
  title: {
    text: '工具使用分布',
    textStyle: { color: '#e5e5e5', fontSize: 14 },
    left: 'center',
  },
  tooltip: {
    trigger: 'item',
    backgroundColor: '#1a1a1a',
    borderColor: '#333',
    textStyle: { color: '#e5e5e5' },
  },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['50%', '55%'],
    data: props.data.map((d, i) => ({
      name: d.tool_name,
      value: d.count,
      itemStyle: { color: colors[i % colors.length] },
    })),
    label: { color: '#a3a3a3', fontSize: 12 },
    labelLine: { lineStyle: { color: '#333' } },
  }],
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
