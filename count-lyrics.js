const fs = require('fs');

// 定义要分析的艺术家列表
const artists = ['杨千嬅', '张国荣'];

// 为每个艺术家创建字符计数对象
artists.forEach(artist => {
  // 读取JSON文件
  const filePath = `./public/assets/${artist}.json`;
  
  try {
    const data = fs.readFileSync(filePath, 'utf8');
    const songs = JSON.parse(data);
    
    // 创建字符计数对象
    const charCount = {};
    
    // 遍历所有歌曲的歌词
    songs.forEach(song => {
      if (song.parsedLyrics && Array.isArray(song.parsedLyrics)) {
        song.parsedLyrics.forEach(line => {
          // 遍历每一行的每个字符
          for (const char of line) {
            // 忽略空格、标点符号等非汉字字符
            if (/[\u4e00-\u9fa5]/.test(char)) {
              charCount[char] = (charCount[char] || 0) + 1;
            }
          }
        });
      }
    });
    
    // 将字符计数转换为数组并排序
    const sortedChars = Object.entries(charCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20); // 获取前20个最常见的字
    
    console.log(`\n${artist}歌词中出现最多的20个字:`);
    sortedChars.forEach((item, index) => {
      console.log(`${index + 1}. 字符: ${item[0]}, 出现次数: ${item[1]}`);
    });
    
    // 找出出现最多的字
    const mostFrequentChar = sortedChars[0];
    console.log(`${artist}歌词中出现最多的字是: "${mostFrequentChar[0]}", 出现了 ${mostFrequentChar[1]} 次`);
  } catch (error) {
    console.error(`处理${artist}的歌词时出错:`, error.message);
  }
}); 