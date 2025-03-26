const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');
const https = require('https');
const { SocksProxyAgent } = require('socks-proxy-agent');

// 排除的角色列表
const EXCLUDED_ROLES = [
  '编曲',
  '制作人',
  '监制',
  'OP',
  'SP',
  '和音',
  '录音',
  '混音',
  'Mastering',
  '编程',
  '键盘',
  '吉他',
  '电吉他',
  '电结他',
  '贝斯',
  '鼓',
  '弦乐编写',
  '铜管乐编写',
  '和声编写',
  '和声',
  '混音师',
  '录音室',
  '混音室',
  '录音工程师',
  '母带后期处理录音师',
  '录音室',
  '母带后期处理录音室',
  '基本轨录音工程',
  '演唱',
  '主唱',
  '作词',
  '作曲',
  '母带',
];

// Apple Music 杨千嬅代表作歌单URL
const appleMusicUrl = 'https://music.apple.com/cn/playlist/%E6%A5%8A%E5%8D%83%E5%AC%85%E4%BB%A3%E8%A1%A8%E4%BD%9C/pl.0fc1d9aeed114d02a4dc9043f275fe8a';

// 网易云音乐API
const neteaseApiUrl = 'https://music.163.com/api/song/lyric';

const socksAgent = new SocksProxyAgent('socks5://127.0.0.1:10808'); 

// 创建一个带有较长超时时间的axios实例
const axiosInstance = axios.create({
  timeout: 30000, // 30秒超时
  httpsAgent: socksAgent
});

/**
 * 获取杨千嬅代表作歌曲列表
 */
async function getSongListFromAppleMusic() {
  console.log('获取歌单...');
  
  // 歌单
  const songs = [
    { order: "1", name: "野孩子", artist: "杨千嬅" },
    { order: "2", name: "勇", artist: "杨千嬅" },
    { order: "3", name: "少女的祈祷", artist: "杨千嬅" },
    { order: "4", name: "可惜我是水瓶座", artist: "杨千嬅" },
    { order: "5", name: "假如让我说下去", artist: "杨千嬅" },
    { order: "6", name: "花与爱丽丝", artist: "杨千嬅" },
    { order: "7", name: "小城大事", artist: "杨千嬅" },
    { order: "8", name: "处处吻", artist: "杨千嬅" },
    { order: "9", name: "飞女正传", artist: "杨千嬅" },
    { order: "10", name: "再见二丁目", artist: "杨千嬅" },
    { order: "11", name: "稀客", artist: "杨千嬅" },
    { order: "12", name: "烈女", artist: "杨千嬅" },
    { order: "13", name: "寒舍", artist: "杨千嬅" },
    { order: "14", name: "还有事情可庆祝", artist: "杨千嬅" },
    { order: "15", name: "偷生", artist: "杨千嬅" },
    { order: "16", name: "炼金术", artist: "杨千嬅" },
    { order: "17", name: "火鸟", artist: "杨千嬅" },
    { order: "18", name: "single", artist: "杨千嬅" },
    { order: "19", name: "最好的债", artist: "杨千嬅" },
    { order: "20", name: "一千零一个", artist: "杨千嬅" },
  ];
  
  return songs;
}

/**
 * 搜索网易云音乐歌曲ID
 */
async function searchSongId(songName, artist) {
  let retryCount = 0;
  const maxRetries = 3;
  
  // 计算两个字符串的相似度
  function similarityRatio(str1, str2) {
    if (!str1 || !str2) return 0;
    
    str1 = str1.toLowerCase();
    str2 = str2.toLowerCase();
    
    const len1 = str1.length;
    const len2 = str2.length;
    
    // 创建矩阵
    const matrix = Array(len1 + 1).fill().map(() => Array(len2 + 1).fill(0));
    
    // 初始化矩阵
    for (let i = 0; i <= len1; i++) matrix[i][0] = i;
    for (let j = 0; j <= len2; j++) matrix[0][j] = j;
    
    // 填充矩阵
    for (let i = 1; i <= len1; i++) {
      for (let j = 1; j <= len2; j++) {
        const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,      // 删除
          matrix[i][j - 1] + 1,      // 插入
          matrix[i - 1][j - 1] + cost // 替换
        );
      }
    }
    
    // 计算相似度
    const distance = matrix[len1][len2];
    const maxLen = Math.max(len1, len2);
    return maxLen > 0 ? (maxLen - distance) / maxLen : 1.0;
  }
  
  // 匹配歌曲和艺术家
  function matchSongArtist(song) {
    return similarityRatio(song.name, songName) >= 0.4 && 
           'artists' in song && 
           similarityRatio(song.artists[0].name, artist) >= 0.4;
  }
  
  // 仅匹配歌曲
  function matchSong(song) {
    return similarityRatio(song.name, songName) >= 0.1;
  }
  
  while (retryCount < maxRetries) {
    try {
      console.log(`搜索歌曲 "${songName}" (尝试 ${retryCount + 1}/${maxRetries})...`);
      
      // 构建搜索URL
      const query = `${artist} "${songName}"`;
      const searchUrl = `https://music.163.com/api/search/get/web?csrf_token=&s=${encodeURIComponent(query)}&type=1&offset=0&limit=5`;
      
      const { data } = await axiosInstance.get(searchUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Referer': 'https://music.163.com/'
        }
      });
      if (data.code === 200 && data.result && data.result.songs && data.result.songs.length > 0) {
        // 过滤匹配歌曲和艺术家的结果
        const matchedSongs = data.result.songs.filter(matchSongArtist);
        
        if (matchedSongs.length > 0) {
          // 找到最小ID的歌曲
          const song = matchedSongs.reduce((min, song) => song.id < min.id ? song : min, matchedSongs[0]);
          console.log(`找到匹配的歌曲: ${song.name} - ${song.artists[0].name} (ID: ${song.id})`);
          return song.id;
        }
        
        // 如果没有找到匹配的歌曲和艺术家，尝试只匹配歌曲
        console.log(`未找到匹配的歌曲和艺术家，尝试只匹配歌曲...`);
        const fallbackUrl = `https://music.163.com/api/search/get/web?csrf_token=&s=${encodeURIComponent(songName)}&type=1&offset=0&limit=10`;
        const fallbackResponse = await axiosInstance.get(fallbackUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://music.163.com/'
          }
        });
        
        if (fallbackResponse.data.code === 200 && 
            fallbackResponse.data.result && 
            fallbackResponse.data.result.songs && 
            fallbackResponse.data.result.songs.length > 0) {
          
          // 过滤匹配歌曲的结果
          const matchedSongs = fallbackResponse.data.result.songs.filter(matchSong);
          
          if (matchedSongs.length > 0) {
            // 找到最小ID的歌曲
            const song = matchedSongs.reduce((min, song) => song.id < min.id ? song : min, matchedSongs[0]);
            console.log(`找到匹配的歌曲: ${song.name} (ID: ${song.id})`);
            return song.id;
          }
          
          // 如果还是找不到，返回第一个结果
          console.log(`未找到匹配的歌曲，使用第一个结果: ${fallbackResponse.data.result.songs[0].name} (ID: ${fallbackResponse.data.result.songs[0].id})`);
          return fallbackResponse.data.result.songs[0].id;
        }
      }
      
      retryCount++;
      if (retryCount < maxRetries) {
        console.log(`搜索失败，等待3秒后重试...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    } catch (error) {
      retryCount++;
      console.error(`搜索歌曲 "${songName}" 失败 (尝试 ${retryCount}/${maxRetries}):`, error.message);
      
      if (retryCount < maxRetries) {
        console.log(`搜索出错，等待3秒后重试...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    }
  }
  
  console.log(`未能找到歌曲 "${songName}" 的ID`);
  return null;
}

/**
 * 获取歌词
 */
async function getLyrics(songId) {
  if (!songId) return null;
  
  let retryCount = 0;
  const maxRetries = 3;
  
  while (retryCount < maxRetries) {
    try {
      console.log(`获取歌词 (ID: ${songId}) (尝试 ${retryCount + 1}/${maxRetries})...`);
      
      const url = `${neteaseApiUrl}?id=${songId}&lv=-1&kv=-1&tv=-1`;
      const { data } = await axiosInstance.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Referer': 'https://music.163.com/'
        }
      });
      
      if (data.code === 200 && data.lrc && data.lrc.lyric) {
        // 处理歌词，过滤掉包含EXCLUDED_ROLES的行
        const lrcLines = data.lrc.lyric.split('\n');
        const filteredLyrics = lrcLines.filter(line => {
          // 过滤掉空行和<br>标签
          if (!line.trim() || line.includes('<br>')) {
            return false;
          }
          
          // 过滤掉包含EXCLUDED_ROLES的行
          for (const role of EXCLUDED_ROLES) {
            if (line.includes(role)) {
              return false;
            }
          }
          
          return true;
        }).join('\n');
        
        return {
          lrc: filteredLyrics,
        };
      }
      
      retryCount++;
      if (retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    } catch (error) {
      retryCount++;
      console.error(`获取歌词失败 (ID: ${songId}) (尝试 ${retryCount}/${maxRetries}):`, error.message);
    }
  }
  
  return null;
}

/**
 * 解析歌词时间轴，去掉时间戳只保留歌词文本
 */
function parseLyricTimeline(lrc) {
  if (!lrc) return [];
  
  const lines = lrc.split('\n');
  const timelineRegex = /\[(\d{2}):(\d{2})\.(\d{2,3})\]/;
  const parsedLyrics = [];
  
  // 处理歌词，去掉时间戳
  for (const line of lines) {
    // 去掉时间戳，只保留歌词文本
    const text = line.replace(timelineRegex, '').trim();
    // 将普通空格替换为全角空格
    const textWithFullWidthSpaces = text.replace(/ /g, '　');
    // 只添加非空歌词
    if (textWithFullWidthSpaces) {
      parsedLyrics.push(textWithFullWidthSpaces);
    }
  }
  
  return parsedLyrics;
}

/**
 * 主函数
 */
async function main() {
  try {
    console.log('===== 杨千嬅代表作歌词获取工具 =====');
    console.log('开始获取歌词...');
    
    // 获取歌曲列表
    const songs = await getSongListFromAppleMusic();
    
    console.log(`共获取到 ${songs.length} 首歌曲，开始获取歌词...`);
    
    // 获取每首歌的歌词
    const songsWithLyrics = [];
    let successCount = 0;
    
    for (let i = 0; i < songs.length; i++) {
      const song = songs[i];
      console.log(`\n[${i+1}/${songs.length}] 正在处理: ${song.name}`);
      
      try {
        // 搜索歌曲ID
        const songId = await searchSongId(song.name, song.artist);
        if (!songId) {
          console.log(`未找到歌曲 "${song.name}" 的ID，跳过获取歌词`);
          songsWithLyrics.push({
            ...song,
            id: null,
            lyrics: null,
            parsedLyrics: []
          });
          continue;
        }
        
        console.log(`找到歌曲 "${song.name}" 的ID: ${songId}`);
        
        // 获取歌词
        const lyrics = await getLyrics(songId);
        
        if (!lyrics || !lyrics.lrc) {
          console.log(`未获取到歌曲 "${song.name}" 的歌词`);
          songsWithLyrics.push({
            ...song,
            id: songId,
            lyrics: null,
            parsedLyrics: []
          });
          continue;
        }
        
        // 解析歌词时间轴
        const parsedLyrics = parseLyricTimeline(lyrics.lrc);
        
        songsWithLyrics.push({
          ...song,
          id: songId,
          lyrics: lyrics,
          parsedLyrics: parsedLyrics
        });
        
        successCount++;
        console.log(`成功获取歌曲 "${song.name}" 的歌词，共 ${parsedLyrics.length} 行`);
      } catch (songError) {
        console.error(`处理歌曲 "${song.name}" 时出错:`, songError.message);
        songsWithLyrics.push({
          ...song,
          id: null,
          lyrics: null,
          parsedLyrics: []
        });
      }
      
      // 避免请求过于频繁
      if (i < songs.length - 1) {
        console.log('等待3秒后处理下一首歌...');
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    }
    
    // 保存结果到JSON文件
    const outputPath = path.join(__dirname, './public/assets/yangqianhua-best-songs.json');
    fs.writeFileSync(outputPath, JSON.stringify(songsWithLyrics, null, 2), 'utf8');
    
    console.log('\n===== 处理完成 =====');
    console.log(`共处理 ${songs.length} 首歌曲，成功获取 ${successCount} 首歌词`);
    console.log(`结果已保存到: ${outputPath}`);
  } catch (error) {
    console.error('程序执行失败:', error.message);
  }
}

// 执行主函数
main(); 