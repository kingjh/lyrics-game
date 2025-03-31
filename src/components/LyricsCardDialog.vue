<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:model-value="$emit('update:modelValue', $event)"
    width="100%"
    height="100%"
    fullscreen
    persistent
    :class="['lyrics-card-dialog', themeClass]"
  >
    <v-card :class="['lyrics-card', themeClass]" style="height: 100%;">
      <v-card-title :class="['text-h5', 'text-center', themeClass]">
        歌詞卡片
      </v-card-title>
      
      <v-card-text class="d-flex">
        <div v-if="isLoading" class="loading-container text-center align-center justify-center flex-column" style="width: 100%; height: 300px;">
          <v-progress-circular indeterminate :color="themeColor" size="64"></v-progress-circular>
          <p class="mt-3">生成中...</p>
        </div>
        
        <div v-else-if="htmlContent" class="html-container w-100" v-html="htmlContent"></div>
        
        <div v-else class="error-container">
          <p>生成失敗，請重試</p>
        </div>
      </v-card-text>
      
      <v-card-actions class="justify-center pb-4">
        <v-btn :color="themeColor" @click="downloadCard" :disabled="isLoading">
          保存圖片
        </v-btn>
        <v-btn 
          :color="themeClass === 'red-theme' ? 'error' : 'secondary'" 
          @click="$emit('update:modelValue', false)" 
          class="ml-2"
          :disabled="isLoading"
        >
          關閉
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, onMounted, watch } from 'vue'
import axios from 'axios'
import html2canvas from 'html2canvas'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  lyrics: {
    type: String,
    required: true
  },
  fullSongLyrics: {
    type: String,
    default: ''
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

const emit = defineEmits(['update:modelValue'])

const isLoading = ref(true)
const htmlContent = ref('')
// 添加緩存對象來存儲生成過的歌詞卡片
const lyricsCache = ref(new Map())
// 緩存大小限制
const MAX_CACHE_SIZE = 20

// 添加緩存管理函數
const addToCache = (key: string, value: string) => {
  // 如果緩存已滿，刪除最早添加的項目
  if (lyricsCache.value.size >= MAX_CACHE_SIZE) {
    const firstKey = lyricsCache.value.keys().next().value
    lyricsCache.value.delete(firstKey)
    console.log('緩存已滿，刪除最早項目:', firstKey)
  }
  // 添加新項目到緩存
  lyricsCache.value.set(key, value)
}

// 监听弹窗和歌词变化
watch(
  () => [props.modelValue, props.lyrics],
  ([newModelValue, newLyrics]) => {
    console.log('watch triggered - modelValue:', newModelValue, 'lyrics:', newLyrics)
    if (newModelValue && newLyrics) {
      generateLyricsCard()
    }
  }
)

onMounted(() => {
  console.log('props.modelValue', props.modelValue)
  if (props.modelValue && props.lyrics) {
    generateLyricsCard()
  }
})

// 生成歌词卡片
const generateLyricsCard = async () => {
  try {
    isLoading.value = true
    htmlContent.value = '' // 清空之前的内容
    
    console.log('开始生成歌词卡片，歌词:', props.lyrics)
    
    if (!props.lyrics || props.lyrics.trim().length === 0) {
      throw new Error('歌词内容为空')
    }
    
    // 处理歌词文本，确保格式合适，不截断歌词
    let processedLyrics = props.lyrics.trim()
    
    // 如果歌词太短，可能不够有意义
    if (processedLyrics.length < 5) {
      console.warn('歌词内容过短，可能无法生成良好结果')
    }
    
    console.log('处理后的完整歌词:', processedLyrics)
    
    // 檢查緩存中是否已有該歌詞卡片
    // 使用歌詞+主題作為緩存鍵，這樣可以處理同一歌詞在不同主題下的情況
    const cacheKey = `${processedLyrics}_${props.themeClass}`
    if (lyricsCache.value.has(cacheKey)) {
      console.log('從緩存中獲取歌詞卡片')
      htmlContent.value = lyricsCache.value.get(cacheKey)
      isLoading.value = false
      return
    }
    
    // 尝试从processedLyrics中提取歌名和歌词部分，确保不截断歌词
    let songName = ""
    let lyricsFragment = processedLyrics
    let fullLyrics = processedLyrics
    let completeSongLyrics = props.fullSongLyrics ? props.fullSongLyrics.trim() : ""
    
    // 如果内容包含 " - "，可能是 "歌名 - 歌词" 的格式
    if (processedLyrics.includes(' - ')) {
      const parts = processedLyrics.split(' - ')
      songName = parts[0].trim()
      lyricsFragment = parts.slice(1).join(' - ').trim() // 确保取得完整歌词，不会因为歌词中也有 " - " 而截断
      
      // 创建更加结构化的提示，清晰表明这是歌词片段
      fullLyrics = `【歌曲名】${songName}\n【歌词片段】"${lyricsFragment}"`
      
      // 如果有完整歌词，则添加
      if (completeSongLyrics) {
        fullLyrics += `\n\n【完整歌词】\n${completeSongLyrics}`
      }
      
      fullLyrics += `\n\n这是歌曲《${songName}》中的一段歌词，请基于这段歌词的意境创作卡片。`
    } else {
      // 如果没有明确的歌名-歌词格式，提示这是一段歌词
      fullLyrics = `【歌词片段】"${processedLyrics}"`
      
      // 如果有完整歌词，则添加
      if (completeSongLyrics) {
        fullLyrics += `\n\n【完整歌词】\n${completeSongLyrics}`
      }
      
      fullLyrics += `\n\n这是一首歌中的一段歌词，请基于这段歌词的意境创作卡片。`
    }
    
    const prompt = `
初始化：
根据用户输入的歌词内容，先把歌词的核心主题翻译成英文（要有押韵感），然后用150字以内的故事（引用著名文学或影视作品）拆解歌词中的深层含义和情感。
然后用HTML创建一个优雅的文字卡片表现这段歌词的意境。

设计要求：
1.所有輸出的中文必須爲繁體中文，禁止使用簡體中文。
2.主题字体不要超过24px大小，正文使用16px左右。
3.卡片背景风格素雅，模仿纸张质感。
4.主题颜色用'${props.themeColor}'
5.卡片padding为24px。
6.添加轻微的纹理或图案作为背景，增强纸张质感。

卡片结构：
1.顶部显示且只显示提供的歌词片段
2.中间是对歌词片段的英文翻译或诠释（要有诗意和押韵感）
3.主体内容为对歌词深层含义的拆解(150字以内的故事，引用著名文学或影视作品）

重要说明：我已提供了歌词片段和完整歌词（如有）。请务必综合考虑整首歌的上下文和情感，避免仅基于片段做出片面理解。在创作时注重表达歌词的整体意境和情感。以下是内容：
""" 
${fullLyrics}
"""
`
    
    try {
      // 尝试调用Gemini API生成HTML内容
      const htmlData = await requestGeminiHTML(prompt)
      console.log('获取到HTML数据，长度:', htmlData.length)
      
      // 將生成的卡片緩存起來
      addToCache(cacheKey, htmlData)
      
      // 延迟一点设置HTML内容，确保DOM已经准备好
      setTimeout(() => {
        htmlContent.value = htmlData
        console.log('HTML内容已设置')
      }, 100)
    } catch (apiError) {
      console.error('API请求失败，使用备用卡片:', apiError)
      // 使用备用方案生成简单的卡片
      const fallbackHtml = generateFallbackCard(processedLyrics)
      // 也將備用卡片緩存起來
      addToCache(cacheKey, fallbackHtml)
      htmlContent.value = fallbackHtml
    }
    
  } catch (error: any) {
    console.error('生成卡片失败:', error)
    htmlContent.value = `<div style="text-align:center;padding:20px;font-family:sans-serif;">
    <h2 style="color:red">生成失敗</h2>
    <p>${error.message || '未知錯誤'}</p>
    </div>`
  } finally {
    isLoading.value = false
  }
}

// 生成备用卡片HTML
const generateFallbackCard = (lyrics: string) => {
  // 创建一个简单的英文转换 (这只是一个非常基础的模拟)
  const generateEnglishTranslation = (text: string) => {
    // 这里只是一个非常简单的模拟
    return `"${text}" in English`;
  };
  
  // 生成一个简单的故事
  const generateStory = () => {
    return "正如《紅樓夢》中所言：「世事洞明皆學問，人情練達即文章。」這句歌詞蘊含著人生的真諦，教會我們感受當下，珍惜所擁有的一切。";
  };
  
  // 选择一个颜色基于主题
  const cardColor = props.themeClass === 'purple-theme' ? '#9575cd' : '#ef5350';
  
  return `
  <div style="font-family: 'Microsoft YaHei', 'SimSun', sans-serif; background-color: #fff; color: #333; padding: 20px; border-radius: 10px; width: 90%; max-width: 600px; margin: 0 auto; box-shadow: 0 8px 30px rgba(0,0,0,0.1); position: relative; overflow: hidden; background-image: url('data:image/svg+xml;utf8,<svg xmlns=&quot;http://www.w3.org/2000/svg&quot; width=&quot;100&quot; height=&quot;100&quot; opacity=&quot;0.05&quot;><rect x=&quot;0&quot; y=&quot;0&quot; width=&quot;100&quot; height=&quot;100&quot; fill=&quot;none&quot; stroke=&quot;%23${cardColor.slice(1)}&quot; stroke-width=&quot;1&quot;/></svg>');">
    <div style="position: absolute; top: 0; left: 0; right: 0; height: 5px; background: linear-gradient(90deg, ${cardColor}88, ${cardColor}55);"></div>
    
    <h1 style="font-size: 24px; text-align: center; margin-bottom: 15px; color: ${cardColor}; font-weight: bold; word-break: break-word;">${lyrics}</h1>
    
    <p style="font-size: 16px; text-align: center; margin-bottom: 20px; font-style: italic; color: #666;">${generateEnglishTranslation(lyrics)}</p>
    
    <div style="font-size: 14px; line-height: 1.6; text-align: justify; margin-top: 20px; padding: 15px; background-color: rgba(255,255,255,0.8); border-left: 4px solid ${cardColor}; border-radius: 0 8px 8px 0; word-break: break-word;">
      ${generateStory()}
    </div>
    
    <div style="font-size: 12px; text-align: right; margin-top: 20px; color: #999;">
      歌詞卡片 • ${new Date().toLocaleDateString('zh-TW')}
    </div>
  </div>
  `
}

// 调用Gemini API生成HTML
const requestGeminiHTML = async (prompt: string, retryCount = 0) => {
  try {
    console.log('发送Gemini请求...尝试次数:', retryCount + 1)
    const url = `https://gai.cfworker.cfd?model=gemini-2.0-flash-thinking-exp-01-21`
    
    // 確保prompt沒有被截斷
    console.log('Prompt總長度:', prompt.length)
    console.log('Prompt前100個字符:', prompt.substring(0, 100))
    console.log('Prompt最後100個字符:', prompt.substring(prompt.length - 100))
    
    const data = {
      contents: [{
        role: 'user',
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        responseMimeType: 'text/plain',
      },
    }
    
    console.log('请求数据:', JSON.stringify(data))
    const response = await axios.post(url, data, { 
      timeout: 600000, // 增加到600秒
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('API响应:', response.data)
    
    if (response.data && 
        response.data.candidates && 
        response.data.candidates[0] && 
        response.data.candidates[0].content && 
        response.data.candidates[0].content.parts) {
      
      // 查找text部分的HTML内容
      const textPart = response.data.candidates[0].content.parts.find((part: any) => part.text);
      
      if (textPart && textPart.text) {
        console.log('找到文本部分:', textPart.text.substring(0, 100) + '...')
        
        // 从文本中提取HTML代码
        const htmlMatch = textPart.text.match(/```html\s*([\s\S]*?)\s*```/);
        if (htmlMatch && htmlMatch[1]) {
          console.log('提取到HTML代码')
          return fixHtmlContent(htmlMatch[1].trim());
        } else {
          // 可能是纯HTML，不包含markdown代码块
          console.log('未找到HTML代码块，使用原始文本')
          return fixHtmlContent(textPart.text);
        }
      } else {
        throw new Error('API返回中未找到HTML数据')
      }
    } else {
      throw new Error('API返回格式不正确')
    }
  } catch (error: any) {
    console.error('API请求失败:', error)
    
    // 错误重试逻辑
    if (retryCount < 2) { // 最多重试2次
      console.log(`请求失败，${error.message}，尝试重试...`)
      
      // 当遇到超时错误时，特别提示
      if (error.message && error.message.includes('timeout')) {
        console.log('遇到超时错误，增加等待时间后重试')
      }
      
      // 等待时间递增
      const waitTime = (retryCount + 1) * 2000
      await new Promise(resolve => setTimeout(resolve, waitTime))
      
      // 递归调用自身进行重试
      return requestGeminiHTML(prompt, retryCount + 1)
    }
    
    // 如果重试次数用完，则抛出错误
    throw error
  }
}

// 修复和包装HTML内容，限制尺寸
const fixHtmlContent = (html: string) => {
  // 如果内容不是HTML格式，将其包装为HTML
  if (!html.trim().startsWith('<')) {
    return `<div style="font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; width: 100%; overflow-wrap: break-word;">${html}</div>`;
  }
  
  // 确保HTML有基本样式
  let fixedHtml = html;
  
  // 查找并替换可能导致溢出的样式
  fixedHtml = fixedHtml.replace(/font-size\s*:\s*\d+px/g, (match) => {
    const size = parseInt(match.replace(/[^0-9]/g, ''));
    if (size > 28) return `font-size: 28px`;
    return match;
  });
  
  // 添加宽度限制和换行
  fixedHtml = fixedHtml.replace(/<div/g, '<div style="max-width: 100%; overflow-wrap: break-word;"');
  
  // 如果没有包含样式的外层div，添加一个
  if (!fixedHtml.includes('style=')) {
    fixedHtml = `<div style="font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; max-width: 100%; overflow-wrap: break-word;">${fixedHtml}</div>`;
  }
  
  return fixedHtml;
};

// 下载卡片为图片
const downloadCard = async () => {
  try {
    const container = document.querySelector('.html-container');
    console.log('html容器元素:', container);
    if (!container) {
      alert('找不到HTML內容容器，無法保存');
      return;
    }
    
    console.log('开始生成图片...');
    
    // 检测浏览器环境
    const isWechat = /MicroMessenger/i.test(navigator.userAgent);
    const isIOS = /(iPhone|iPad|iPod)/i.test(navigator.userAgent);
    const isAndroid = /Android/i.test(navigator.userAgent);
    const isMobile = isIOS || isAndroid;
    
    console.log('浏览器环境:', { 
      isWechat, 
      isIOS, 
      isAndroid, 
      isMobile 
    });
    
    // 首先克隆容器并设置手机屏幕宽度
    const cloneContainer = container.cloneNode(true) as HTMLElement;
    document.body.appendChild(cloneContainer);
    
    // 设置克隆元素的样式，使其不可见但保持原始布局
    cloneContainer.style.position = 'absolute';
    cloneContainer.style.top = '-9999px';
    cloneContainer.style.width = '320px'; // 修改为更窄的手机宽度
    cloneContainer.style.maxWidth = '320px';
    cloneContainer.style.overflow = 'hidden';
    cloneContainer.style.transformOrigin = 'top left';
    cloneContainer.style.margin = '0'; // 确保没有margin
    
    // 为内部内容添加padding
    const contentDiv = cloneContainer.querySelector('div');
    if (contentDiv) {
      contentDiv.style.padding = '24px 20px';
      contentDiv.style.boxSizing = 'border-box';
    }
    
    // 等待一会儿让布局渲染完成
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 获取原始容器在手机上的宽度
    const mobileWidth = cloneContainer.clientWidth;
    const mobileHeight = cloneContainer.clientHeight;
    
    console.log('手机视图尺寸:', mobileWidth, 'x', mobileHeight);
    
    // 使用html2canvas渲染克隆的容器
    const canvas = await html2canvas(cloneContainer, {
      scale: 2, // 提高清晰度
      useCORS: true,
      logging: true,
      backgroundColor: '#FFFFFF',
      width: mobileWidth,
      height: mobileHeight,
      onclone: (doc) => {
        console.log('HTML克隆完成，高度:', mobileHeight);
      }
    });
    
    // 移除克隆的元素
    document.body.removeChild(cloneContainer);
    
    console.log('图片生成完成，准备下载');
    
    // 获取canvas数据
    const imgData = canvas.toDataURL('image/png');
    
    // 创建新图像以处理最终输出
    const finalImg = new Image();
    finalImg.src = imgData;
    
    finalImg.onload = () => {
      // 确保输出图像与手机屏幕比例相同
      const outputCanvas = document.createElement('canvas');
      
      // 使用与手机屏幕相同的比例
      const outputWidth = mobileWidth * 2; // 640px (高DPI)
      const outputHeight = mobileHeight * 2;
      
      outputCanvas.width = outputWidth;
      outputCanvas.height = outputHeight;
      
      const ctx = outputCanvas.getContext('2d');
      if (ctx) {
        // 绘制白色背景
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, outputWidth, outputHeight);
        
        // 直接绘制图像，保持原始尺寸和位置，不添加额外边距
        ctx.drawImage(finalImg, 0, 0, outputWidth, outputHeight);
        
        const finalImgData = outputCanvas.toDataURL('image/png');
        
        // 通用预览和保存方法 - 在所有设备上都使用此方法
        const showPreviewOverlay = () => {
          const overlay = document.createElement('div');
          overlay.style.position = 'fixed';
          overlay.style.top = '0';
          overlay.style.left = '0';
          overlay.style.width = '100%';
          overlay.style.height = '100%';
          overlay.style.backgroundColor = 'rgba(0,0,0,0.8)';
          overlay.style.zIndex = '9999';
          overlay.style.display = 'flex';
          overlay.style.flexDirection = 'column';
          overlay.style.alignItems = 'center';
          overlay.style.justifyContent = 'center';
          
          const imgElement = document.createElement('img');
          imgElement.src = finalImgData;
          imgElement.style.maxWidth = '90%';
          imgElement.style.maxHeight = '80%';
          imgElement.style.objectFit = 'contain';
          imgElement.style.padding = '0 20px'; // 确保图片左右有内边距
          
          const tipElement = document.createElement('div');
          
          if (isWechat || isMobile) {
            tipElement.textContent = '請長按圖片保存到相冊';
          } else {
            tipElement.textContent = '右鍵點擊圖片，選擇"圖片另存為..."保存';
          }
          
          tipElement.style.color = 'white';
          tipElement.style.fontSize = '16px';
          tipElement.style.marginTop = '20px';
          tipElement.style.textAlign = 'center';
          
          const buttonContainer = document.createElement('div');
          buttonContainer.style.display = 'flex';
          buttonContainer.style.gap = '10px';
          buttonContainer.style.marginTop = '20px';
          
          // 关闭按钮
          const closeButton = document.createElement('button');
          closeButton.textContent = '關閉';
          closeButton.style.padding = '8px 20px';
          closeButton.style.backgroundColor = '#ffffff';
          closeButton.style.border = 'none';
          closeButton.style.borderRadius = '4px';
          closeButton.style.color = '#333';
          closeButton.onclick = () => document.body.removeChild(overlay);
          
          // 下载按钮 (仅在非移动设备上显示)
          if (!isMobile) {
            const downloadButton = document.createElement('button');
            downloadButton.textContent = '下載圖片';
            downloadButton.style.padding = '8px 20px';
            downloadButton.style.backgroundColor = props.themeColor === 'primary' ? '#9575cd' : '#ef5350';
            downloadButton.style.border = 'none';
            downloadButton.style.borderRadius = '4px';
            downloadButton.style.color = '#fff';
            downloadButton.onclick = () => {
              try {
                const link = document.createElement('a');
                link.download = `lyrics-card-${Date.now()}.png`;
                link.href = finalImgData;
                link.click();
              } catch (error) {
                console.error('下载按钮点击失败:', error);
                alert('下載失敗，請嘗試右鍵保存圖片');
              }
            };
            buttonContainer.appendChild(downloadButton);
          }
          
          buttonContainer.appendChild(closeButton);
          
          overlay.appendChild(imgElement);
          overlay.appendChild(tipElement);
          overlay.appendChild(buttonContainer);
          document.body.appendChild(overlay);
        };
        
        // 尝试直接下载 (桌面浏览器)
        if (!isMobile && !isWechat) {
          try {
            const link = document.createElement('a');
            link.download = `lyrics-card-${Date.now()}.png`;
            link.href = finalImgData;
            link.click();
            
            // 即使直接下载成功，也提供预览界面，因为很多浏览器会拦截下载
            setTimeout(() => {
              showPreviewOverlay();
            }, 500);
          } catch (error) {
            console.error('自动下载失败，回退到预览模式:', error);
            showPreviewOverlay();
          }
        } else {
          // 移动端或微信浏览器直接使用预览界面
          showPreviewOverlay();
        }
      }
    };
  } catch (error) {
    console.error('下载图片失败:', error);
    alert('保存失敗，請重試：' + (error instanceof Error ? error.message : '未知錯誤'));
  }
};
</script>

<style scoped>
.lyrics-card-dialog::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(4px);
  z-index: -1;
}
</style>