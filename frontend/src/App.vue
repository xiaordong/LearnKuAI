<script setup lang="ts">
import { NConfigProvider, NLayout, darkTheme, type GlobalThemeOverrides } from 'naive-ui'
import TopNav from './components/TopNav.vue'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#3b82f6',
    primaryColorHover: '#2563eb',
    borderRadius: '8px',
  },
}
</script>

<template>
  <NConfigProvider :theme="darkTheme" :theme-overrides="themeOverrides">
    <NLayout style="height: 100vh; background: #0a0a0a">
      <TopNav />
      <RouterView />
    </NLayout>
  </NConfigProvider>
</template>
