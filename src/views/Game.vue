<template>
  <v-main :class="['game-main', themeClass]">
    <v-container fluid class="pa-0 fill-height">
      <v-row no-gutters class="fill-height">
        <v-col cols="12">
          <v-card-title :class="['justify-center', 'game-title', themeClass]">
            <h1 class="text-h4 font-weight-bold text-center">{{ GAME_NAME }}</h1>
          </v-card-title>
          <v-card-subtitle style="white-space: pre-line;" :class="['game-subtitle', 'font-weight-bold', 'mt-4', 'mx-4', themeClass]">
            {{ gameMessage }}
          </v-card-subtitle>
          <v-card-actions class="justify-center flex-column" v-if="isGameOver">
            <v-btn 
              :color="themeColor" 
              @click="showResultDialog = true"
              class="view-score-btn"
            >
              查看成绩
            </v-btn>
          </v-card-actions>
          <v-card-text>
            <v-row justify="center">
              <v-chip class="ma-2 status-chip" :color="themeColor" outlined>
                还可以弄断 {{ MAX_BROKEN_SCROLLS_COUNT - brokenCount }} 支签
              </v-chip>
              <v-chip class="ma-2 status-chip" :color="themeColor" outlined>
                总拉出字数: {{ wordCount }}
              </v-chip>
            </v-row>
          </v-card-text>
          
          <v-card-text class="flex-grow-1 d-flex align-center justify-center">
            <div :class="['scrolls-container', themeClass]">
              <scroll-item
                v-for="(scroll, index) in scrolls"
                :key="index"
                :scroll="scroll"
                :is-game-over="isGameOver"
                :theme-color="themeColor"
                :theme-class="themeClass"
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
      :artist="artist"
      :theme-color="themeColor"
      :theme-class="themeClass"
      @restart="restartGame"
    />

    <!-- 加载遮罩 -->
    <v-dialog
      v-model="isLoading"
      persistent
      width="300"
      content-class="loading-dialog"
      overlay-opacity="0.8"
    >
      <v-card :color="themeColor" dark class="text-center pa-4">
        <v-progress-circular indeterminate color="white" size="64"></v-progress-circular>
        <p class="mt-3 white--text">加载中...</p>
      </v-card>
    </v-dialog>

    <!-- 返回按钮 -->
    <div class="back-button">
      <v-btn 
        :color="themeColor" 
        fab
        small
        @click="goBack"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
    </div>
  </v-main>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { remToPx } from '@/ults/index'
import ScrollItem from '@/components/ScrollItem.vue'
import ResultDialog from '@/components/ResultDialog.vue'
import { debounce } from 'lodash-es'
import { useRoute, useRouter } from 'vue-router'

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
const GAME_NAME = '热字切歌'
const route = useRoute()
const router = useRouter()

// 从路由参数获取主题和热字
const artist = ref(route.params.artist as string || '杨千嬅')
const hotWord = ref(route.query.hotWord as string || '我')
const themeColor = ref(route.query.theme as string || 'primary')
const themeClass = computed(() => {
  return themeColor.value === 'red' ? 'red-theme' : 'purple-theme'
})

const INIT_MESSAGE = computed(() => {
  return `下面是一些签筒，筒外是歌名，筒里装着的是这歌某句歌词的签。\n可以推拉把手控制歌词。\n出现"${hotWord.value}"字的话这签会断掉，不能再推拉了！\n断${MAX_BROKEN_SCROLLS_COUNT}支签后游戏结束（点击歌词有惊喜），拉出的歌词越多越厉害！`
})

// 拖动减速系数，值越小拖动越慢
const dragSpeedFactor = 0.7

// 状态
const songs = ref<Song[]>([])
const scrolls = ref<Scroll[]>([])
const brokenScrolls = ref<Scroll[]>([])
const collectedLyrics = ref<string[]>([])
const brokenCount = ref(0)
const wordCount = ref(0)
const isGameOver = ref(false)
const gameMessage = ref('')
const showResultDialog = ref(false)
const isLoading = ref(false)

// 拖动状态
const isDragging = ref(false)
const dragScrollIndex = ref(-1)
const startX = ref(0)
const startWidth = ref(0)

// 存储事件处理函数的引用
const mouseMoveHandler = (e: Event) => drag(e as MouseEvent)
const touchMoveHandler = (e: Event) => drag(e as TouchEvent)

// 方法
const loadSongs = async () => {
  try {
    // 根据选择的歌手加载不同的JSON文件
    const jsonFile = artist.value === '张国荣' ? '/assets/张国荣.json' : '/assets/杨千嬅.json'
    const response = await fetch(jsonFile)
    const data = await response.json()
    
    // 使用 Web Worker 处理数据
    const hotWordValue = hotWord.value; // 先获取热字值
    console.log("当前热字:", hotWordValue);
    const workerCode = `
      self.onmessage = function(e) {
        const songs = e.data.songs;
        const hotWord = "${hotWordValue}"; // 使用双引号包裹变量
        
        console.log("开始处理歌曲数据，热字:", hotWord);
        
        if (!songs || !Array.isArray(songs)) {
          console.error("没有收到有效的歌曲数据");
          self.postMessage([]);
          return;
        }
        
        try {
          console.log("接收到歌曲数量:", songs.length);
          
          // 处理歌曲数据，确保每首歌都有歌名和歌词
          const processedSongs = songs
            .filter(song => 
              song && 
              typeof song.name === 'string' && 
              song.parsedLyrics && 
              Array.isArray(song.parsedLyrics) && 
              song.parsedLyrics.length > 0
            )
            .map(song => {
              // 从parsedLyrics中查找包含热字的歌词行
              let foundLyric = null;
              
              // 首先尝试找包含热字的行
              for (let i = 0; i < song.parsedLyrics.length; i++) {
                const line = song.parsedLyrics[i];
                if (line.length > 5 && line.includes(hotWord) && line.indexOf(hotWord) > 1) {
                  foundLyric = line;
                  break;
                }
              }
              
              // 如果没找到包含热字的行，返回null表示不选择这首歌
              if (!foundLyric) {
                return null;
              }
              
              return {
                name: song.name.trim(),
                lyrics: foundLyric.trim()
              };
            })
            .filter(song => song !== null) // 过滤掉没有热字的歌
          
          console.log("处理后的歌曲数量:", processedSongs.length);
          
          // 将处理后的数据发送回主线程
          self.postMessage(processedSongs);
        } catch (error) {
          console.error('处理歌曲数据时出错:', error);
          self.postMessage([]);
        }
      };
    `;
    
    const blob = new Blob([workerCode], { type: 'application/javascript' });
    const worker = new Worker(URL.createObjectURL(blob));
    worker.postMessage({ songs: data })
    
    return new Promise<void>((resolve, reject) => {
      worker.onmessage = (e) => {
        const filteredSongs = e.data as Song[]
        songs.value = shuffleArray(filteredSongs).slice(0, 8)
        createScrolls()
        resolve()
      }
      
      worker.onerror = (error) => {
        console.error('Worker error:', error)
        gameMessage.value = '加载游戏数据失败，请刷新页面重试。'
        reject(error)
      }
    })
  } catch (error) {
    console.error('加载游戏数据失败:', error)
    gameMessage.value = '加载游戏数据失败，请刷新页面重试。'
    throw error
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

const drag = debounce((e: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return

  if (scrolls.value[dragScrollIndex.value]?.isBroken) return
  
  const currentX = e.type === 'mousemove' ? (e as MouseEvent).clientX : (e as TouchEvent).touches[0].clientX
  const diffX = startX.value - currentX
  const scroll = scrolls.value[dragScrollIndex.value]
  
  // 计算新宽度，应用减速系数
  const adjustedDiffX = diffX * dragSpeedFactor
  const newWidth = Math.max(INIT_WIDTH, Math.min(scroll.maxWidth, startWidth.value + adjustedDiffX))
  
  // 更新宽度
  scrolls.value[dragScrollIndex.value].width = newWidth
  
  // 更新文本
  updateVisibleText(dragScrollIndex.value)
  
  e.preventDefault()
}, 8) // 缩短等待时间到8ms，提高响应速度

// 更新文本的函数
const updateVisibleText = debounce((index: number) => {
  const scroll = scrolls.value[index]
  if (!scroll) return
  
  const visibleChars = Math.floor((scroll.width - INIT_WIDTH) / PIXELS_PER_CHAR)
  
  wordCount.value -= scroll.visibleText.replace(/\s/g, '').length
  // 提取歌词，不再转换空格
  const rawText = visibleChars <= 0 ? '' : scroll.lyrics.substring(0, visibleChars)
  scroll.visibleText = rawText
  wordCount.value += scroll.visibleText.replace(/\s/g, '').length
  
  // 立即检查是否包含热字
  if (scroll.visibleText.includes(hotWord.value)) {
    breakScroll(index)
  }
}, 8) // 缩短等待时间到8ms，提高响应速度

const endDrag = () => {
  isDragging.value = false
  dragScrollIndex.value = -1
}

const checkForBreakingChar = (index: number) => {
  const scroll = scrolls.value[index]
  
  if (scroll.isBroken) return
  
  if (scroll.visibleText.includes(hotWord.value)) {
    breakScroll(index)
  }
}

const breakScroll = (index: number) => {
  const scroll = scrolls.value[index]
  
  scrolls.value[index].isBroken = true
  brokenScrolls.value.push(scroll)
  brokenCount.value++
  collectedLyrics.value.push(scroll.visibleText) // 已经转换过空格的文本
  
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
  isLoading.value = true
  brokenScrolls.value = []
  collectedLyrics.value = []
  brokenCount.value = 0
  wordCount.value = 0
  isGameOver.value = false
  showResultDialog.value = false
  gameMessage.value = INIT_MESSAGE.value
  
  // 直接加载新歌曲，不使用嵌套的setTimeout
  loadSongs()
    .finally(() => {
      setTimeout(() => {
        isLoading.value = false
      }, 300) // 保留短暂延迟以确保渲染完成
    })
}

// 返回主页
const goBack = () => {
  router.push({ name: 'Home' })
}

// 生命周期钩子
onMounted(() => {
  isLoading.value = true
  gameMessage.value = INIT_MESSAGE.value
  loadSongs()
    .finally(() => {
      setTimeout(() => {
        isLoading.value = false
      }, 300)
    })
  
  document.addEventListener('mousemove', mouseMoveHandler)
  document.addEventListener('touchmove', touchMoveHandler, { passive: false })
  document.addEventListener('mouseup', endDrag)
  document.addEventListener('touchend', endDrag)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', mouseMoveHandler)
  document.removeEventListener('touchmove', touchMoveHandler)
  document.removeEventListener('mouseup', endDrag)
  document.removeEventListener('touchend', endDrag)
})
</script>

<style scoped>
/* 游戏相关样式 */
.game-main {
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.game-main.purple-theme {
  background: radial-gradient(circle, #f0ebfd, #e6e0fa);
}

.game-main.red-theme {
  background: radial-gradient(circle, #ffebee, #ffcdd2);
}

/* 加载对话框样式 */
:deep(.loading-dialog) {
  background: transparent !important;
  box-shadow: none !important;
}

:deep(.v-card.loading-dialog) {
  border-radius: 16px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
}

.game-title {
  color: white !important;
  padding: 16px !important;
  margin-bottom: 5px;
}

.game-title.purple-theme {
  background: linear-gradient(to right, #9575cd, #7e57c2) !important;
}

.game-title.red-theme {
  background: linear-gradient(to right, #ef5350, #e53935) !important;
}

.game-subtitle {
  padding: 10px 15px !important;
  border-radius: 8px;
  margin: 0 15px 5px 15px;
  font-size: 0.9rem !important;
}

.game-subtitle.purple-theme {
  background: linear-gradient(to right, #e6e0fa, #d4c6f5) !important;
  border: 1px solid #b39ddb;
}

.game-subtitle.red-theme {
  background: linear-gradient(to right, #ffebee, #ffcdd2) !important;
  border: 1px solid #ef9a9a;
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
  padding: 0 16px !important;
}

.scrolls-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  width: 100%;
  max-width: 500px;
  padding: 15px;
  border-radius: 12px;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
  contain: content;
  content-visibility: auto;
}

.scrolls-container.purple-theme {
  background: radial-gradient(circle, #f8f5fe, #f0ebfd);
  border: 1px solid #d4c6f5;
  scrollbar-color: #b39ddb transparent;
}

.scrolls-container.red-theme {
  background: radial-gradient(circle, #fff5f5, #ffebee);
  border: 1px solid #ffcdd2;
  scrollbar-color: #ef9a9a transparent;
}

.scrolls-container::-webkit-scrollbar {
  width: 6px;
}

.scrolls-container::-webkit-scrollbar-track {
  background: transparent;
}

.scrolls-container.purple-theme::-webkit-scrollbar-thumb {
  background-color: #b39ddb;
  border-radius: 6px;
}

.scrolls-container.red-theme::-webkit-scrollbar-thumb {
  background-color: #ef9a9a;
  border-radius: 6px;
}

.scroll-item {
  will-change: transform;
  transform: translateZ(0);
  backface-visibility: hidden;
  perspective: 1000px;
  contain: content;
  content-visibility: auto;
}

.back-button {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
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
  
  .back-button {
    top: 10px;
    left: 10px;
  }
}

/* 优化触摸设备性能 */
@media (hover: none) {
  .scroll-item {
    touch-action: pan-x;
    -webkit-tap-highlight-color: transparent;
  }
  
  .scrolls-container {
    -webkit-overflow-scrolling: touch;
  }
}
</style> 