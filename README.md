# 杨千嬅演唱会曲目歌词爬取工具

这个工具用于从维基百科获取杨千嬅MY TREE OF LIVE世界巡回演唱会的曲目列表，并从网易云音乐获取对应的歌词信息，最终将数据保存为JSON格式。

## 功能特点

- 自动从维基百科爬取演唱会曲目列表
- 通过网易云音乐API搜索歌曲并获取歌词
- 解析歌词时间轴信息
- 将所有数据保存为结构化的JSON文件

## 安装

1. 确保已安装Node.js环境（建议v14.0.0或更高版本）
2. 克隆或下载本项目
3. 在项目目录中运行以下命令安装依赖：

```bash
npm install
```

## 代理配置

由于维基百科和网易云音乐API在某些地区可能无法直接访问，本工具支持使用HTTP代理。默认配置如下：

```javascript
// 代理配置
const PROXY_CONFIG = {
  host: '127.0.0.1',
  port: 10809,
  protocol: 'http'
};

// 是否启用代理
const USE_PROXY = true;
```

您可以根据自己的网络环境修改这些配置：

1. 如果您不需要使用代理，可以将`USE_PROXY`设置为`false`
2. 如果您需要使用代理，请确保代理服务器正在运行，并根据实际情况修改`host`、`port`和`protocol`

常见的代理客户端默认端口：
- Clash: 7890
- V2Ray: 10809
- Shadowsocks: 1080

## 使用方法

### 使用启动脚本（推荐）

#### Windows用户
直接双击运行`start.bat`文件，或在命令提示符中执行：

```bash
start.bat
```

#### Linux/macOS用户
首先给脚本添加执行权限：

```bash
chmod +x start.sh
```

然后执行：

```bash
./start.sh
```

### 手动运行

或者，您也可以手动运行以下命令启动爬取程序：

```bash
npm start
```

或者直接运行：

```bash
node lyrics-scraper.js
```

程序执行完成后，将在项目目录下生成`yangqianhua-concert-songs.json`文件，包含所有歌曲信息和歌词。

## 数据结构

生成的JSON文件包含以下结构：

```json
[
  {
    "order": "序号",
    "name": "歌曲名称",
    "artist": "杨千嬅",
    "id": "网易云音乐ID",
    "lyrics": {
      "lrc": "原始歌词",
      "tlyric": "翻译歌词（如有）",
      "klyric": "原文歌词（如有）"
    },
    "parsedLyrics": [
      {
        "time": 时间点（秒）,
        "text": "歌词文本"
      }
    ]
  }
]
```

## 网络连接问题解决方案

如果遇到类似 `connect ETIMEDOUT 199.16.158.9:443` 的错误，这通常是由于网络连接问题导致的，特别是在访问维基百科时可能会遇到。以下是一些解决方案：

### 1. 检查网络连接
确保您的网络连接正常，可以尝试在浏览器中打开维基百科页面看是否能正常访问。

### 2. 配置代理服务器
如果您在中国大陆或其他无法直接访问维基百科的地区，需要使用代理服务器。本工具已内置代理支持，您只需修改`lyrics-scraper.js`文件开头的代理配置：

```javascript
// 代理配置
const PROXY_CONFIG = {
  host: '127.0.0.1',  // 修改为您的代理服务器地址
  port: 10809,        // 修改为您的代理服务器端口
  protocol: 'http'    // 代理协议，通常为http
};

// 是否启用代理
const USE_PROXY = true;  // 设置为true启用代理
```

确保您的代理服务器（如Clash、V2Ray、Shadowsocks等）正在运行，并且配置了正确的端口。

### 3. 使用备用歌曲列表
脚本已内置备用歌曲列表，如果无法从维基百科获取曲目，将自动使用备用列表。您也可以手动编辑脚本中的备用歌曲列表，添加您知道的杨千嬅演唱会曲目。

### 4. 增加超时时间
如果网络较慢，可以尝试增加请求超时时间：

```javascript
// 在lyrics-scraper.js文件中找到以下代码
const axiosInstance = axios.create({
  timeout: 30000, // 30秒超时
  ...(USE_PROXY ? { proxy: PROXY_CONFIG } : {}),
  httpsAgent: new https.Agent({ 
    rejectUnauthorized: false // 忽略SSL证书验证
  })
});

// 修改为更长的超时时间，例如60秒
const axiosInstance = axios.create({
  timeout: 60000, // 60秒超时
  ...(USE_PROXY ? { proxy: PROXY_CONFIG } : {}),
  httpsAgent: new https.Agent({ 
    rejectUnauthorized: false // 忽略SSL证书验证
  })
});
```

## 注意事项

- 网络请求可能会受到限制，如遇到请求失败，可以稍后再试
- 部分歌曲可能在网易云音乐中找不到，或者歌词不完整
- 程序会自动尝试多种API获取歌词，以提高成功率
- 如果遇到网络问题，程序会自动重试多次，并在失败后使用备用方案
- 在中国大陆使用时，通常需要配置代理服务器才能正常访问维基百科

## 参考资料

- 维基百科页面：[杨千嬅MY TREE OF LIVE世界巡回演唱会](https://zh.wikipedia.org/wiki/%E6%A5%8A%E5%8D%83%E5%AC%85MY_TREE_OF_LIVE%E4%B8%96%E7%95%8C%E5%B7%A1%E8%BF%B4%E6%BC%94%E5%94%B1%E6%9C%83)
- 网易云音乐API 