<template>
  <v-main class="game-main">
    <v-container fluid class="pa-0 fill-height">
      <v-row no-gutters class="fill-height">
        <v-col cols="12">
          <v-card-title class="justify-center game-title">
            <h1 class="text-h4 font-weight-bold text-center">{{ GAME_NAME }}</h1>
          </v-card-title>
          <v-card-subtitle style="white-space: pre-line;" class="game-subtitle font-weight-bold mt-4 mx-4">
            {{ gameMessage }}
          </v-card-subtitle>
          <v-card-actions class="justify-center flex-column" v-if="isGameOver">
            <v-btn 
              color="primary" 
              @click="showResultDialog = true"
              class="view-score-btn"
            >
              查看成绩
            </v-btn>
          </v-card-actions>
          <v-card-text>
            <v-row justify="center">
              <v-chip class="ma-2 status-chip" color="primary" outlined>
                还可以弄断 {{ MAX_BROKEN_SCROLLS_COUNT - brokenCount }} 支签
              </v-chip>
              <v-chip class="ma-2 status-chip" color="primary" outlined>
                总拉出字数: {{ wordCount }}
              </v-chip>
            </v-row>
          </v-card-text>
          
          <v-card-text class="flex-grow-1 d-flex align-center justify-center">
            <div class="scrolls-container">
              <scroll-item
                v-for="(scroll, index) in scrolls"
                :key="index"
                :scroll="scroll"
                :is-game-over="isGameOver"
                @start-drag="handleStartDrag"
              />
            </div>
          </v-card-text>
        </v-col>
      </v-row>
    </v-container>
    
    <!-- 结果对话框 -->
    <result-dialog
      v-model="showResultDialog"
      :broken-count="brokenCount"
      :word-count="wordCount"
      :broken-scrolls="brokenScrolls"
      :collected-lyrics="collectedLyrics"
      :game-name="GAME_NAME"
      @restart="restartGame"
    />
  </v-main>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { remToPx } from '@/ults/index'
import ScrollItem from '@/components/ScrollItem.vue'
import ResultDialog from '@/components/ResultDialog.vue'

// 类型定义
interface Song {
  name: string;
  lyrics: string;
}

interface Scroll {
  name: string;
  lyrics: string;
  width: number;
  maxWidth: number;
  isBroken: boolean;
  visibleText: string;
  index: number;
}

// 常量
const PIXELS_PER_CHAR = 14
const INIT_WIDTH = 136
const MAX_BROKEN_SCROLLS_COUNT = 3
const GAME_NAME = '千fa抽签'
const INIT_MESSAGE = `下面是一些签筒，筒外是歌名，筒里装着的是这歌某句歌词的签。\n可以推拉把手控制歌词。\n出现"我"字的话这签会断掉，不能再推拉了！\n断${MAX_BROKEN_SCROLLS_COUNT}支签后游戏结束，拉出的歌词越多越厉害！`

// 状态
const songs = ref<Song[]>([])
const scrolls = ref<Scroll[]>([])
const brokenScrolls = ref<Scroll[]>([])
const collectedLyrics = ref<string[]>([])
const brokenCount = ref(0)
const wordCount = ref(0)
const isGameOver = ref(false)
const gameMessage = ref(INIT_MESSAGE)
const showResultDialog = ref(false)

// 拖动状态
const isDragging = ref(false)
const dragScrollIndex = ref(-1)
const startX = ref(0)
const startWidth = ref(0)

// 方法
const loadSongs = async () => {
  try {
    const response = await fetch('/assets/yangqianhua-best-songs.json')
    const data = await response.json()
    
    const filteredSongs: Song[] = []
    
    data.forEach((song: any, idx) => {
      const parsedLyrics = [...song.parsedLyrics]
      
      // 查找包含"我"字且"我"不是第一或第二个字的歌词行
      for (let i = 0; i < parsedLyrics.length; i++) {
        const text = parsedLyrics[i]
        const woIndex = text.indexOf('我')
        
        // 检查是否包含"我"字，且"我"不是第一或第二个字
        
        if (woIndex > 1) {
          // 找到符合条件的歌词，截取这句和之后的所有歌词
          const selectedLyrics = parsedLyrics.slice(i).join('')
                   
          filteredSongs.push({
            name: song.name,
            lyrics: selectedLyrics,
          })
          
          // 处理完这首歌，跳出循环
          break
        }
      }
    })
    
    // 随机选择9首歌并打乱顺序
    songs.value = shuffleArray(filteredSongs).slice(0, 9)
    
    createScrolls()
  } catch (error) {
    console.error('加载游戏数据失败:', error)
    gameMessage.value = '加载游戏数据失败，请刷新页面重试。'
  }
}

// 打乱数组顺序的辅助函数
const shuffleArray = <T>(array: T[]): T[] => {
  const newArray = [...array]
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[newArray[i], newArray[j]] = [newArray[j], newArray[i]]
  }
  return newArray
}

const createScrolls = () => {
  scrolls.value = songs.value.map((song, index) => ({
    name: song.name,
    lyrics: song.lyrics,
    width: INIT_WIDTH,
    maxWidth: screen.width - remToPx(2),
    isBroken: false,
    visibleText: '',
    index: index,
  }))
}

const handleStartDrag = ({ event, index }: { event: MouseEvent | TouchEvent, index: number }) => {
  if (scrolls.value[index].isBroken || isGameOver.value) return
  
  isDragging.value = true
  dragScrollIndex.value = index
  startX.value = event.type === 'mousedown' ? (event as MouseEvent).clientX : (event as TouchEvent).touches[0].clientX
  startWidth.value = scrolls.value[index].width
  
  event.preventDefault()
}

const drag = (e: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return

  if (scrolls.value[dragScrollIndex.value] && scrolls.value[dragScrollIndex.value].isBroken) return
  
  const currentX = e.type === 'mousemove' ? (e as MouseEvent).clientX : (e as TouchEvent).touches[0].clientX
  const diffX = startX.value - currentX
  const scroll = scrolls.value[dragScrollIndex.value]
  
  let newWidth = Math.max(INIT_WIDTH, Math.min(scroll.maxWidth, startWidth.value + diffX))
  
  scrolls.value[dragScrollIndex.value].width = newWidth
  updateVisibleText(dragScrollIndex.value)
  checkForBreakingChar(dragScrollIndex.value)
  
  e.preventDefault()
}

const endDrag = () => {
  isDragging.value = false
  dragScrollIndex.value = -1
}

const updateVisibleText = (index: number) => {
  const scroll = scrolls.value[index]
  const visibleChars = Math.floor((scroll.width - INIT_WIDTH) / PIXELS_PER_CHAR)
  
  wordCount.value -= scrolls.value[index].visibleText.length
  if (visibleChars <= 0) {
    scrolls.value[index].visibleText = ''
  } else {
    scrolls.value[index].visibleText = scroll.lyrics.substring(0, visibleChars)
  }
  wordCount.value += scrolls.value[index].visibleText.length
}

const checkForBreakingChar = (index: number) => {
  const scroll = scrolls.value[index]
  
  if (scroll.isBroken) return
  
  if (scroll.visibleText.includes('我')) {
    breakScroll(index)
  }
}

const breakScroll = (index: number) => {
  const scroll = scrolls.value[index]
  
  scrolls.value[index].isBroken = true
  brokenScrolls.value.push(scroll)
  brokenCount.value++
  collectedLyrics.value.push(scroll.visibleText)
  
  checkGameOver()
}

const checkGameOver = () => {
  if (brokenCount.value >= 3 && !isGameOver.value) {
    isGameOver.value = true
    showResultDialog.value = true
    gameMessage.value = '游戏结束！点击按钮查看成绩。'
  }
}

const restartGame = () => {
  loadSongs()
  brokenScrolls.value = []
  collectedLyrics.value = []
  brokenCount.value = 0
  wordCount.value = 0
  isGameOver.value = false
  showResultDialog.value = false
  
  createScrolls()
  gameMessage.value = INIT_MESSAGE
}

// 生命周期钩子
onMounted(() => {
  loadSongs()
  
  document.addEventListener('mousemove', drag as (e: Event) => void)
  document.addEventListener('touchmove', drag as (e: Event) => void, { passive: false })
  document.addEventListener('mouseup', endDrag)
  document.addEventListener('touchend', endDrag)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', drag as (e: Event) => void)
  document.removeEventListener('touchmove', drag as (e: Event) => void)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchend', endDrag)
})
</script>

<style scoped>
/* 游戏相关样式 */
.game-main {
  background: radial-gradient(circle, #f0ebfd, #e6e0fa);
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.game-title {
  background: linear-gradient(to right, #9575cd, #7e57c2) !important;
  color: white !important;
  padding: 16px !important;
  margin-bottom: 5px;
}

.game-subtitle {
  background: linear-gradient(to right, #e6e0fa, #d4c6f5) !important;
  padding: 10px 15px !important;
  border-radius: 8px;
  margin: 0 15px 5px 15px;
  border: 1px solid #b39ddb;
  font-size: 0.9rem !important;
}

.view-score-btn {
  padding: 0 25px !important;
  height: 45px !important;
  margin-top: 5px;
  border-radius: 16px !important;
  min-width: 120px !important;
  font-weight: bold !important;
}

.status-chip {
  background: linear-gradient(to right, #e6e0fa, #d4c6f5) !important;
  border: 1px solid #9575cd !important;
  padding: 0 16px !important;
}

.scrolls-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 100%;
  max-width: 500px;
  padding: 15px;
  background: radial-gradient(circle, #f8f5fe, #f0ebfd);
  border-radius: 12px;
  border: 1px solid #d4c6f5;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: #b39ddb transparent;
}

.scrolls-container::-webkit-scrollbar {
  width: 6px;
}

.scrolls-container::-webkit-scrollbar-track {
  background: transparent;
}

.scrolls-container::-webkit-scrollbar-thumb {
  background-color: #b39ddb;
  border-radius: 6px;
}

@media (max-width: 768px) {
  .game-title {
    padding: 12px !important;
    margin-bottom: 3px;
  }
  
  .game-subtitle {
    padding: 8px 12px !important;
    margin: 0 10px 3px 10px;
    font-size: 0.85rem !important;
  }

  .scrolls-container {
    padding: 12px;
    gap: 10px;
    max-height: calc(100vh - 180px);
  }
  
  .v-container {
    padding: 0 !important;
  }
  
  .v-col {
    padding: 0 !important;
  }
  
  .status-chip {
    margin: 5px !important;
    font-size: 0.85rem !important;
  }
}
</style> 