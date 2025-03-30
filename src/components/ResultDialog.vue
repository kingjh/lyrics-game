<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
    persistent
    :class="['result-dialog', themeClass]"
  >
    <v-card :class="['result-card', themeClass]">
      <v-card-title :class="['text-h5', 'text-center', themeClass]">
        {{ gameName }}游戏结果
      </v-card-title>
      
      <v-card-text>
        <v-row justify="center">
          <v-col cols="12" sm="6">
            <v-card outlined :class="['score-card', themeClass]">
              <v-card-text class="text-center">
                您断开了 <span class="font-weight-bold">{{ brokenCount }}</span> 支签，总拉出字数: <span class="font-weight-bold">{{ wordCount }}</span>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-divider :class="['my-4', themeClass === 'red-theme' ? 'red-divider' : 'purple-divider']"></v-divider>
        
        <h3 class="text-subtitle-1 font-weight-bold mb-2">断签:</h3>
        <v-card 
          outlined 
          v-for="(scroll, index) in brokenScrolls" 
          :key="scroll?.index || index" 
          :class="['lyric-card', themeClass]"
          @click="showLyricsCard(index, scroll?.name || '')"
          style="cursor: pointer"
        >
          <v-card-text>
            <v-row>
              <v-col cols="7" :class="['text-right', themeClass]">
                {{ collectedLyrics[index] }}
              </v-col>
              <v-col cols="5" :class="themeClass">
                {{ scroll?.name || '' }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>
      
      <v-card-actions class="justify-center pb-4">
        <v-btn :color="themeColor" @click="$emit('restart')">
          重新开始
        </v-btn>
        <v-btn 
          :color="themeClass === 'red-theme' ? 'error' : 'secondary'" 
          @click="$emit('update:modelValue', false)" 
          class="ml-2"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  
  <!-- 歌词卡片弹窗 -->
  <lyrics-card-dialog
    v-model="showLyricsCardDialog"
    :lyrics="selectedLyrics"
    :theme-color="themeColor"
    :theme-class="themeClass"
  />
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, watch } from 'vue'
import axios from 'axios'
import LyricsCardDialog from './LyricsCardDialog.vue'

interface BrokenScroll {
  index: number;
  name: string;
  lyrics?: string;
  visibleText?: string;
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
  },
  artist: {
    type: String,
    default: '杨千嬅'
  },
  themeColor: {
    type: String,
    default: 'primary'
  },
  themeClass: {
    type: String,
    default: 'purple-theme'
  }
})

const emit = defineEmits(['update:modelValue', 'restart'])

// 歌词卡片相关
const showLyricsCardDialog = ref(false)
const selectedLyrics = ref('')

// 监听selectedLyrics变化，确保有内容时才打开弹窗
watch(selectedLyrics, (newValue) => {
  if (newValue) {
    console.log('selectedLyrics已设置，打开弹窗')
  }
})

// 打开歌词卡片对话框
const showLyricsCard = async (index: number, songName: string) => {
  try {
    // 获取最完整的歌词
    const scroll = props.brokenScrolls[index]
    let fullLyric = ''
    
    // 首先尝试使用完整歌词
    if (scroll && scroll.lyrics) {
      fullLyric = scroll.lyrics
      console.log('使用完整歌詞:', fullLyric)
    } 
    // 其次尝试使用歌名搜索歌词（这里只是示例）
    else if (songName && songName.length > 0) {
      console.log('嘗試使用歌名:', songName)
      fullLyric = `${songName} - ${props.collectedLyrics[index] || ''}`
    } 
    // 最后使用收集的部分歌词
    else {
      fullLyric = props.collectedLyrics[index] || ''
      console.log('只能使用部分歌詞:', fullLyric)
    }
    
    if (!fullLyric) {
      throw new Error('無法獲取歌詞')
    }
    
    // 确保内容长度适中(避免太短)
    if (fullLyric.length < 10 && props.collectedLyrics[index]) {
      // 如果太短，添加歌名作为补充
      fullLyric = `${songName || ''} - ${props.collectedLyrics[index]}`
    }
    
    console.log('最終使用的歌詞:', fullLyric)
    selectedLyrics.value = fullLyric
    showLyricsCardDialog.value = true
    console.log('showLyricsCardDialog设置为:', showLyricsCardDialog.value)
    
  } catch (error: any) {
    console.error('打開歌詞卡片失敗:', error)
    alert('無法打開歌詞卡片，請重試')
  }
}
</script>

<style scoped>
.result-dialog::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(4px);
  z-index: -1;
}

.result-dialog.purple-theme::before {
  background: rgba(157, 125, 205, 0.15);
}

.result-dialog.red-theme::before {
  background: rgba(229, 115, 115, 0.15);
}

.result-card {
  border-radius: 20px !important;
  overflow: hidden;
}

.result-card.purple-theme {
  border: 2px solid #9575cd !important;
  box-shadow: 0 8px 25px rgba(147, 117, 205, 0.5) !important;
  background: radial-gradient(circle, #f0ebfd, #e6e0fa) !important;
}

.result-card.red-theme {
  border: 2px solid #e57373 !important;
  box-shadow: 0 8px 25px rgba(229, 115, 115, 0.5) !important;
  background: radial-gradient(circle, #fff8f8, #ffebee) !important;
}

.score-card {
  border-radius: 16px !important;
}

.score-card.purple-theme {
  background: linear-gradient(to right, #e6e0fa, #d4c6f5) !important;
  border: 1px solid #b39ddb !important;
}

.score-card.red-theme {
  background: linear-gradient(to right, #fff8f8, #ffcdd2) !important;
  border: 1px solid #ef9a9a !important;
}

.lyric-card {
  margin-bottom: 8px;
  border-radius: 16px !important;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.lyric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1) !important;
}

.lyric-card.purple-theme {
  border: 1px solid #d4c6f5 !important;
}

.lyric-card.red-theme {
  border: 1px solid #ffcdd2 !important;
}

.lyric-card .v-card-text {
  padding: 0 !important;
}

.lyric-card .v-row {
  margin: 0;
  flex-wrap: nowrap;
}

.text-right.purple-theme {
  background: linear-gradient(to right, #9575cd, white) !important;
  border-radius: 16px 0 0 16px;
  padding: 8px;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

.text-right.red-theme {
  background: linear-gradient(to right, #ef5350, white) !important;
  border-radius: 16px 0 0 16px;
  padding: 8px;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

.v-col.purple-theme:nth-child(2) {
  background: linear-gradient(to left, #9575cd, white) !important;
  border-radius: 0 16px 16px 0;
  padding: 8px;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

.v-col.red-theme:nth-child(2) {
  background: linear-gradient(to left, #ef5350, white) !important;
  border-radius: 0 16px 16px 0;
  padding: 8px;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

.purple-divider {
  border-color: #b39ddb !important;
}

.red-divider {
  border-color: #ef9a9a !important;
}

.v-card-title.purple-theme {
  background: radial-gradient(circle, #9575cd, #7e57c2) !important;
  color: white !important;
  padding: 16px !important;
}

.v-card-title.red-theme {
  background: radial-gradient(circle, #ef5350, #e53935) !important;
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
}

.result-dialog.purple-theme .v-card-text {
  scrollbar-color: #b39ddb transparent;
}

.result-dialog.red-theme .v-card-text {
  scrollbar-color: #ef9a9a transparent;
}

.result-dialog .v-card-text::-webkit-scrollbar {
  width: 6px;
}

.result-dialog .v-card-text::-webkit-scrollbar-track {
  background: transparent;
}

.result-dialog.purple-theme .v-card-text::-webkit-scrollbar-thumb {
  background-color: #b39ddb;
  border-radius: 6px;
}

.result-dialog.red-theme .v-card-text::-webkit-scrollbar-thumb {
  background-color: #ef9a9a;
  border-radius: 6px;
}

/* 图片覆盖层样式 */
.image-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000 !important;
}

.overlay-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 16px;
  width: 100%;
  max-width: 500px;
}

.generated-image {
  max-width: 90vw;
  max-height: 80vh;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  border-radius: 10px;
  object-fit: contain;
}

.overlay-tip {
  color: white;
  margin-top: 15px;
  font-size: 14px;
  background: rgba(0, 0, 0, 0.5);
  padding: 8px 16px;
  border-radius: 20px;
}

.close-btn {
  color: white !important;
  position: absolute;
  top: -40px;
  right: -15px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  width: 100%;
}
</style> 