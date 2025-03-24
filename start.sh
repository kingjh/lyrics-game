#!/bin/bash

echo "杨千嬅演唱会曲目歌词爬取工具"
echo "============================"
echo

echo "正在检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    echo "下载地址: https://nodejs.org/"
    exit 1
fi

echo "正在安装依赖..."
npm install

echo
echo "开始爬取数据..."
node lyrics-scraper.js

echo
echo "程序执行完成" 