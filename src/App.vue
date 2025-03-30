<template>
  <v-app>
    <router-view></router-view>
  </v-app>
</template>

<script setup>
// 根组件不需要任何逻辑
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', sans-serif;
  background-color: #f5f5f5;
  color: #333;
  line-height: 1.6;
  overflow: hidden;
}

.hidden {
  display: none !important;
}

/* 紫色主题 */
.purple-theme {
  --light-purple: #e6e0fa;
  --medium-purple: #d4c6f5;
  --dark-purple: #b39ddb;
  --accent-purple: #9575cd;
  --primary: #7e57c2;
  --secondary: #b39ddb;
}

/* 红色主题 */
.red-theme {
  --light-red: #ffebee;
  --medium-red: #ffcdd2;
  --dark-red: #ef9a9a;
  --accent-red: #ef5350;
  --primary: #e53935;
  --secondary: #ef9a9a;
}

/* 通用按钮样式 */
.v-btn {
  border-radius: 16px !important;
  height: 42px !important;
  min-width: 100px !important;
  font-weight: bold !important;
}

/* 文本颜色 */
.v-card-title, .v-card-subtitle, .theme--light.v-btn {
  color: #424242 !important;
}

/* 消除滚动条 */
.v-application, .v-main, .v-container {
  overflow: hidden !important;
}

@media (max-width: 768px) {
  html, body, .v-application, .v-main, .v-container {
    overflow: hidden !important;
    overscroll-behavior: none;
  }
}
</style> 