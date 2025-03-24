@echo off
echo 杨千嬅演唱会曲目歌词爬取工具
echo ============================
echo.

echo 正在检查Node.js环境...
where node >nul 2>nul
if %errorlevel% neq 0 (
  echo 错误: 未找到Node.js，请先安装Node.js
  echo 下载地址: https://nodejs.org/
  pause
  exit /b
)

echo 正在安装依赖...
call npm install

echo.
echo 开始爬取数据...
call node lyrics-scraper.js

echo.
echo 程序执行完成，按任意键退出
pause 