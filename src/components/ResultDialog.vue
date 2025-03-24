<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
    persistent
    class="result-dialog"
  >
    <v-card class="result-card">
      <v-card-title class="text-h5 text-center">
        千fa抽签游戏结果
      </v-card-title>
      
      <v-card-text>
        <v-row justify="center">
          <v-col cols="12" sm="6">
            <v-card outlined class="score-card">
              <v-card-text class="text-center">
                您断开了 <span class="font-weight-bold">{{ brokenCount }}</span> 支签，总拉出字数: <span class="font-weight-bold">{{ wordCount }}</span>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-divider class="my-4 purple-divider"></v-divider>
        
        <h3 class="text-subtitle-1 font-weight-bold mb-2">断签:</h3>
        <v-card outlined v-for="(scroll, index) in brokenScrolls" :key="scroll?.index || index" class="lyric-card">
          <v-card-text>
            <v-row>
              <v-col cols="7" class="text-right">
                {{ collectedLyrics[index] }}
              </v-col>
              <v-col cols="5">
                {{ scroll?.name || '' }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>
      
      <v-card-actions class="justify-center pb-4">
        <v-btn color="primary" @click="$emit('restart')">
          重新开始
        </v-btn>
        <v-btn 
          color="secondary" 
          @click="$emit('update:modelValue', false)" 
          class="ml-2"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

interface BrokenScroll {
  index: number;
  name: string;
  [key: string]: any;
}

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  brokenCount: {
    type: Number,
    required: true
  },
  wordCount: {
    type: Number,
    required: true
  },
  brokenScrolls: {
    type: Array as () => BrokenScroll[],
    required: true,
    default: () => []
  },
  collectedLyrics: {
    type: Array as () => string[],
    required: true,
    default: () => []
  },
  gameName: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'restart'])
</script>

<style scoped>
.result-dialog::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(157, 125, 205, 0.15);
  backdrop-filter: blur(4px);
  z-index: -1;
}

.result-card {
  border: 2px solid #9575cd !important;
  box-shadow: 0 8px 25px rgba(147, 117, 205, 0.5) !important;
  background: radial-gradient(circle, #f0ebfd, #e6e0fa) !important;
  border-radius: 20px !important;
  overflow: hidden;
}

.score-card {
  background: linear-gradient(to right, #e6e0fa, #d4c6f5) !important;
  border: 1px solid #b39ddb !important;
  border-radius: 16px !important;
}

.lyric-card {
  margin-bottom: 8px;
  border: 1px solid #d4c6f5 !important;
  border-radius: 16px !important;
  overflow: hidden;
}

.lyric-card .v-card-text {
  padding: 0 !important;
}

.lyric-card .v-row {
  margin: 0;
  flex-wrap: nowrap;
}

.lyric-card .text-right {
  background: linear-gradient(to right, #9575cd, white) !important;
  border-radius: 16px 0 0 16px;
  padding: 8px;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

.lyric-card .v-col:nth-child(2) {
  background: linear-gradient(to left, #9575cd, white) !important;
  border-radius: 0 16px 16px 0;
  padding: 8px;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

.purple-divider {
  border-color: #b39ddb !important;
}

.result-dialog .v-card-title {
  background: radial-gradient(circle, #9575cd, #7e57c2) !important;
  color: white !important;
  padding: 16px !important;
}

/* 按钮样式 */
.v-btn {
  border-radius: 16px !important;
  height: 42px !important;
  min-width: 100px !important;
  font-weight: bold !important;
}

/* 结果对话框中的滚动容器 */
.result-dialog .v-card-text {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
  scrollbar-width: thin;
  scrollbar-color: #b39ddb transparent;
}

.result-dialog .v-card-text::-webkit-scrollbar {
  width: 6px;
}

.result-dialog .v-card-text::-webkit-scrollbar-track {
  background: transparent;
}

.result-dialog .v-card-text::-webkit-scrollbar-thumb {
  background-color: #b39ddb;
  border-radius: 6px;
}
</style> 