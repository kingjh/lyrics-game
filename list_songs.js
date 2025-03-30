const fs = require('fs');

try {
  const data = fs.readFileSync('./public/assets/张国荣.json', 'utf8');
  const songs = JSON.parse(data);
  console.log('共有歌曲数量: ' + songs.length);
  console.log('歌曲列表:');
  songs.forEach((song, index) => {
    console.log(`${index + 1}. ${song.name}`);
  });
} catch (err) {
  console.error(err);
}
