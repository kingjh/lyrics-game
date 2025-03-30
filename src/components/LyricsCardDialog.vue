<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="90vw"
    max-height="90vh"
    persistent
    :class="['lyrics-card-dialog', themeClass]"
  >
    <v-card :class="['lyrics-card', themeClass]">
      <v-card-title :class="['text-h5', 'text-center', themeClass]">
        歌詞卡片
      </v-card-title>
      
      <v-card-text class="card-content">
        <div v-if="isLoading" class="loading-container">
          <v-progress-circular indeterminate :color="themeColor" size="64"></v-progress-circular>
          <p class="mt-3">生成中...</p>
        </div>
        
        <div v-else-if="htmlContent" class="html-container" v-html="htmlContent"></div>
        
        <div v-else class="error-container">
          <p>生成失敗，請重試</p>
        </div>
      </v-card-text>
      
      <v-card-actions class="justify-center pb-4">
        <v-btn :color="themeColor" @click="downloadCard">
          保存圖片
        </v-btn>
        <v-btn 
          :color="themeClass === 'red-theme' ? 'error' : 'secondary'" 
          @click="$emit('update:modelValue', false)" 
          class="ml-2"
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
    
    // 处理歌词文本，确保格式合适
    let processedLyrics = props.lyrics.trim()
    
    // 如果歌词太短，可能不够有意义
    if (processedLyrics.length < 5) {
      console.warn('歌词内容过短，可能无法生成良好结果')
    }
    
    // 如果歌词太长，可能会导致生成问题，但不截断
    if (processedLyrics.length > 100) {
      console.warn('歌词内容过长，但不截断')
    }
    
    console.log('处理后的完整歌词:', processedLyrics)
    
    const prompt = `
初始化：
根据用户输入的话题，先把话题翻译成英文，然后用150字以内的故事（引用著名文学或影视作品）拆解其中的深层含义。
然后用HTML创建一个优雅的文字卡片表现这个话题。
设计要求：
1.所有中文字必须使用繁体。
2.主题字体不要超过24px大小，正文使用16px左右。
3.卡片背景风格素雅，模仿纸张质感。
4.主题颜色用'${props.themeColor}'
5.卡片整体宽度不超过90%，避免内容溢出。
6.添加轻微的纹理或图案作为背景，增强纸张质感。

卡片结构：
1.顶部用户输入的话题
2.中间用户输入话题的英文翻译，要押韵
3.主体内容为对话题深层含义的拆解(150字以内的故事，引用著名文学或影视作品）

用户话题为：
""" 
${processedLyrics}
"""
`
    
    try {
      // 尝试调用Gemini API生成HTML内容
      const htmlData = await requestGeminiHTML(prompt)
      console.log('获取到HTML数据，长度:', htmlData.length)
      
      // 延迟一点设置HTML内容，确保DOM已经准备好
      setTimeout(() => {
        htmlContent.value = htmlData
        console.log('HTML内容已设置')
      }, 100)
    } catch (apiError) {
      console.error('API请求失败，使用备用卡片:', apiError)
      // 使用备用方案生成简单的卡片
      const fallbackHtml = generateFallbackCard(processedLyrics)
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
  // 简单的繁体转换
  const simplifiedToTraditional = (text: string) => {
    const map: Record<string, string> = {
      '东': '東', '为': '為', '义': '義', '乐': '樂', '习': '習',
      '书': '書', '云': '雲', '产': '產', '亚': '亞', '从': '從',
      '仅': '僅', '价': '價', '众': '眾', '优': '優', '们': '們',
      '会': '會', '体': '體', '党': '黨', '关': '關', '兴': '興',
      '写': '寫', '农': '農', '冻': '凍', '净': '淨', '准': '準', 
      '减': '減', '凤': '鳳', '几': '幾', '击': '擊', '动': '動', 
      '务': '務', '勋': '勳', '单': '單', '发': '發', '变': '變', 
      '只': '只', '台': '臺', '叶': '葉', '号': '號', '后': '後', 
      '听': '聽', '周': '週', '响': '響', '唤': '喚', '团': '團', 
      '国': '國', '图': '圖', '场': '場', '坏': '壞', '块': '塊', 
      '声': '聲', '复': '復', '备': '備', '头': '頭', '奖': '獎', 
      '妈': '媽', '娘': '孃', '学': '學', '宁': '寧', '实': '實', 
      '家': '家', '宽': '寬', '宾': '賓', '对': '對', '寻': '尋', 
      '导': '導', '层': '層', '岁': '歲', '币': '幣', '师': '師', 
      '带': '帶', '干': '幹', '广': '廣', '应': '應', '开': '開', 
      '异': '異', '张': '張', '弹': '彈', '强': '強', '归': '歸', 
      '当': '當', '录': '錄', '影': '影', '征': '征', '怀': '懷', 
      '态': '態', '恼': '惱', '恋': '戀', '总': '總', '恶': '惡', 
      '悬': '懸', '情': '情', '惯': '慣', '惊': '驚', '想': '想', 
      '意': '意', '感': '感', '愿': '願', '战': '戰', '戏': '戲',
      '戴': '戴', '户': '戶', '房': '房', '所': '所', '扑': '撲',
      '执': '執', '护': '護', '担': '擔', '择': '擇', '拟': '擬', 
      '拥': '擁', '拼': '拚', '持': '持', '挂': '掛', '指': '指', 
      '挥': '揮', '损': '損', '换': '換', '据': '據', '摄': '攝', 
      '摆': '擺', '摇': '搖', '无': '無', '时': '時', '显': '顯', 
      '晓': '曉', '晕': '暈', '晚': '晚', '晰': '晰', '暂': '暫', 
      '曲': '曲', '最': '最', '月': '月', '有': '有', '朱': '朱', 
      '机': '機', '杀': '殺', '来': '來', '杨': '楊', '极': '極', 
      '构': '構', '标': '標', '样': '樣', '气': '氣', '汤': '湯', 
      '没': '沒', '决': '決', '沟': '溝', '况': '況', '温': '溫', 
      '游': '游', '满': '滿', '滨': '濱', '热': '熱', '焕': '煥', 
      '爱': '愛', '爷': '爺', '状': '狀', '独': '獨', '狮': '獅', 
      '环': '環', '现': '現', '球': '球', '理': '理', '琼': '瓊', 
      '电': '電', '画': '畫', '痴': '癡', '皱': '皺', '盘': '盤',
      '确': '確', '碍': '礙', '种': '種', '稳': '穩', '穷': '窮',
      '竞': '競', '笔': '筆', '筑': '築', '签': '簽', '简': '簡',
      '类': '類', '粮': '糧', '系': '系', '级': '級', '纪': '紀',
      '约': '約', '纲': '綱', '纳': '納', '纯': '純', '纵': '縱',
      '练': '練', '终': '終', '经': '經', '绘': '繪', '给': '給',
      '网': '網', '罗': '羅', '罚': '罰', '美': '美', '翻': '翻',
      '职': '職', '联': '聯', '肤': '膚', '胜': '勝', '脏': '臟',
      '脑': '腦', '脸': '臉', '腾': '騰', '自': '自', '舰': '艦',
      '艺': '藝', '节': '節', '芬': '芬', '花': '花', '苏': '蘇',
      '范': '範', '荐': '薦', '获': '獲', '莱': '萊', '萨': '薩',
      '营': '營', '药': '藥', '落': '落', '虑': '慮', '虚': '虛',
      '补': '補', '袭': '襲', '见': '見', '观': '觀', '规': '規',
      '视': '視', '览': '覽', '觉': '覺', '角': '角', '触': '觸',
      '计': '計', '让': '讓', '记': '記', '设': '設', '许': '許', 
      '证': '證', '评': '評', '识': '識', '词': '詞', '试': '試', 
      '说': '說', '请': '請', '读': '讀', '课': '課', '谁': '誰', 
      '调': '調', '论': '論', '财': '財', '贝': '貝', '责': '責', 
      '贴': '貼', '资': '資', '输': '輸', '达': '達', '过': '過', 
      '远': '遠', '进': '進', '运': '運', '这': '這', '连': '連', 
      '逻': '邏', '邮': '郵', '邻': '鄰', '采': '採', '释': '釋', 
      '里': '裡', '钟': '鐘', '钱': '錢', '铁': '鐵', '银': '銀', 
      '链': '鏈', '销': '銷', '锁': '鎖', '锋': '鋒', '锦': '錦', 
      '长': '長', '门': '門', '闪': '閃', '问': '問', '闲': '閒', 
      '间': '間', '队': '隊', '难': '難', '雇': '僱', '静': '靜', 
      '颖': '穎', '风': '風', '飞': '飛', '养': '養', '馆': '館', 
      '驰': '馳', '驱': '驅', '驶': '駛', '验': '驗', '鱼': '魚', 
      '鲁': '魯', '鲜': '鮮', '鸟': '鳥', '鸡': '雞', '鸿': '鴻', 
      '鹏': '鵬', '麦': '麥', '黄': '黃', '齐': '齊', '齿': '齒', 
      '龄': '齡', '龙': '龍'
    };
    
    return [...text].map(char => map[char] || char).join('');
  };
  
  const traditionalLyrics = simplifiedToTraditional(lyrics);
  
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
    
    <h1 style="font-size: 24px; text-align: center; margin-bottom: 15px; color: ${cardColor}; font-weight: bold; word-break: break-word;">${traditionalLyrics}</h1>
    
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
    const url = `https://gai.cfworker.cfd?model=gemini-2.5-pro-exp-03-25`
    
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
      timeout: 120000, // 增加到120秒
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
    return `<div style="font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; max-width: 100%; overflow-wrap: break-word;">${html}</div>`;
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
    const canvas = await html2canvas(container as HTMLElement, {
      scale: 2, // 提高清晰度
      useCORS: true,
      logging: true,
      backgroundColor: null,
      onclone: (doc) => {
        console.log('HTML克隆完成');
      }
    });
    
    console.log('图片生成完成，准备下载');
    // 创建下载链接
    const link = document.createElement('a');
    link.download = `lyrics-card-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    
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