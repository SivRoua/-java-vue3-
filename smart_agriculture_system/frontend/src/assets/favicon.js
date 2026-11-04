// 创建一个简单的绿色植物图标作为网站favicon
export function createFavicon() {
  // 创建canvas元素
  const canvas = document.createElement('canvas');
  canvas.width = 32;
  canvas.height = 32;
  
  const ctx = canvas.getContext('2d');
  
  // 绘制背景
  ctx.fillStyle = '#f1f8e9'; // 浅绿色背景
  ctx.fillRect(0, 0, 32, 32);
  
  // 绘制植物茎
  ctx.fillStyle = '#33691e'; // 深绿色
  ctx.fillRect(14, 10, 4, 22);
  
  // 绘制叶子
  ctx.fillStyle = '#7cb342'; // 绿色
  
  // 左叶
  ctx.beginPath();
  ctx.ellipse(8, 12, 8, 5, Math.PI / 4, 0, 2 * Math.PI);
  ctx.fill();
  
  // 右叶
  ctx.beginPath();
  ctx.ellipse(24, 12, 8, 5, -Math.PI / 4, 0, 2 * Math.PI);
  ctx.fill();
  
  // 顶叶
  ctx.beginPath();
  ctx.ellipse(16, 5, 5, 8, 0, 0, 2 * Math.PI);
  ctx.fill();
  
  // 将canvas转换为URL
  const dataUrl = canvas.toDataURL('image/png');
  
  // 创建或更新favicon链接
  let link = document.querySelector('link[rel="icon"]');
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = dataUrl;
}

// 导出默认函数，以便在主入口文件中调用
export default createFavicon; 