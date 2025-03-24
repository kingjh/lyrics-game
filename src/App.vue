<template>
  <v-app class="purple-theme">
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

.purple-theme {
  --light-purple: #e6e0fa;
  --medium-purple: #d4c6f5;
  --dark-purple: #b39ddb;
  --accent-purple: #9575cd;
  
  background: var(--light-purple);
}

/* 扁长形状使用线性渐变 */
.v-card, .v-chip, .v-btn {
  background: linear-gradient(to right, var(--light-purple), var(--medium-purple)) !important;
  border-color: var(--dark-purple) !important;
}

/* 正方形/接近正方形的形状使用径向渐变 */
.v-card.square, .v-avatar, .v-dialog .v-card {
  background: radial-gradient(circle, var(--light-purple), var(--medium-purple)) !important;
}

/* 强调色 */
.v-btn.primary {
  background: linear-gradient(to right, var(--dark-purple), var(--accent-purple)) !important;
  color: white !important;
  border-radius: 16px !important; /* 按钮圆角矩形 */
}

.v-btn.secondary {
  background: linear-gradient(to right, var(--medium-purple), var(--dark-purple)) !important;
  color: #424242 !important;
  border-radius: 16px !important; /* 按钮圆角矩形 */
}

/* 所有按钮圆角矩形 */
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

/* 给对话框添加特殊样式 */
.v-dialog .v-card {
  border: 2px solid var(--accent-purple) !important;
  border-radius: 20px !important;
  overflow: hidden;
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