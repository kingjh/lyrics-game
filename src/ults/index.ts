/**
 * 将 rem 转换为像素
 * @param rem rem值
 * @returns 像素值
 */
export function remToPx(rem: number): number {
  // 获取html根元素的字体大小
  const fontSize = parseFloat(getComputedStyle(document.documentElement).fontSize)
  return rem * fontSize
}

