interface Song {
  name: string;
  lyrics: string;
}

self.onmessage = (e) => {
  const { songs } = e.data;
  const filteredSongs: Song[] = [];
  
  songs.forEach((song: any) => {
    const parsedLyrics = [...song.parsedLyrics];
    
    // 查找包含"我"字且"我"不是第一或第二个字的歌词行
    for (let i = 0; i < parsedLyrics.length; i++) {
      const text = parsedLyrics[i];
      const woIndex = text.indexOf('我');
      
      if (woIndex > 1) {
        // 找到符合条件的歌词，截取这句和之后的所有歌词
        const selectedLyrics = parsedLyrics.slice(i).join('');
        
        filteredSongs.push({
          name: song.name,
          lyrics: selectedLyrics,
        });
        
        break;
      }
    }
  });
  
  self.postMessage(filteredSongs);
}; 