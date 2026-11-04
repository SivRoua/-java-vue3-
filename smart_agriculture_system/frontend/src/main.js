import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/styles/index.css'  // 导入全局样式
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent, 
  DataZoomComponent,
  TitleComponent,
  ToolboxComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import createFavicon from './assets/favicon'
import * as echarts from 'echarts'

// 禁用开发环境日志
if (process.env.NODE_ENV === 'production') {
  console.log = () => {}
  console.warn = () => {}
  console.error = () => {}
  console.info = () => {}
  console.debug = () => {}
}

// 启用性能指标收集
let loadTime = Date.now()

// 添加安全的数组操作方法
const safeArrayMethods = () => {
  // 保护includes方法
  const originalIncludes = Array.prototype.includes;
  Array.prototype.includes = function(...args) {
    if (!this) return false;
    return originalIncludes.apply(this, args);
  };
  
  // 保护reduce方法
  const originalReduce = Array.prototype.reduce;
  Array.prototype.reduce = function(...args) {
    if (!this || this.length === 0) {
      // 如果是空数组且提供了初始值，返回初始值
      if (args.length >= 2) {
        return args[1];
      }
      // 否则返回默认值
      return null;
    }
    return originalReduce.apply(this, args);
  };
  
  // 保护map方法
  const originalMap = Array.prototype.map;
  Array.prototype.map = function(...args) {
    if (!this) return [];
    return originalMap.apply(this, args);
  };
  
  // 保护filter方法
  const originalFilter = Array.prototype.filter;
  Array.prototype.filter = function(...args) {
    if (!this) return [];
    return originalFilter.apply(this, args);
  };
};

// 应用安全数组方法
safeArrayMethods();

// 全局错误处理
window.addEventListener('error', (event) => {
  // 避免在控制台重复显示错误
  if (event.error && event.error.message && (
      event.error.message.includes('is not a function') ||
      event.error.message.includes('Cannot read property') ||
      event.error.message.includes('null') ||
      event.error.message.includes('undefined')
    )) {
    event.preventDefault();
  }
  return false;
});

window.addEventListener('unhandledrejection', (event) => {
  return false;
});

// 预加载核心资源
const preloadResources = () => {
  // 预加载主要图标和字体
  const resources = [
    '/favicon.ico', 
    '/logo.svg'
  ]
  
  resources.forEach(url => {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = url
    link.as = url.endsWith('.svg') ? 'image' : 'image'
    document.head.appendChild(link)
  })
}

// 初始化localStorage检查
try {
  // 确保localStorage可用
  localStorage.setItem('test', 'test')
  localStorage.removeItem('test')
  
  // 确保存储的JSON是有效的
  const userInfoStr = localStorage.getItem('userInfo')
  if (userInfoStr && typeof userInfoStr === 'string') {
    try {
      JSON.parse(userInfoStr)
    } catch (e) {
      localStorage.removeItem('userInfo')
    }
  }
} catch (e) {
  // localStorage不可用，静默处理
}

// 创建动态favicon
try {
  createFavicon()
} catch (e) {
  // 创建favicon失败，静默处理
}

// 注册 ECharts 组件
try {
  use([
    CanvasRenderer,
    LineChart,
    BarChart,
    PieChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    DataZoomComponent,
    TitleComponent,
    ToolboxComponent
  ])
} catch (e) {
  // 注册ECharts组件失败，静默处理
  console.error('ECharts组件注册失败:', e)
}

// 创建ECharts辅助插件
const echartsPlugin = {
  install(app) {
    // 全局挂载echarts实例，方便访问
    app.config.globalProperties.$echarts = echarts
    
    // 安全地执行echarts方法
    const safeEchartsMethod = (instance, methodName, ...args) => {
      if (!instance) return null
      
      try {
        if (typeof instance[methodName] === 'function') {
          return instance[methodName](...args)
        }
        return null
      } catch (e) {
        console.warn(`执行echarts.${methodName}失败:`, e)
        return null
      }
    }
    
    // 提供一个确保图表渲染成功的全局方法
    app.config.globalProperties.$ensureChartRender = (chartRef, options, retries = 3) => {
      if (!chartRef || !chartRef.value) return null
      
      try {
        // 确保DOM元素存在且有尺寸
        if (chartRef.value.clientWidth === 0 || chartRef.value.clientHeight === 0) {
          if (retries > 0) {
            setTimeout(() => {
              app.config.globalProperties.$ensureChartRender(chartRef, options, retries - 1)
            }, 200)
          }
          return null
        }
        
        // 初始化图表
        const chart = echarts.init(chartRef.value)
        
        // 安全地设置选项
        safeEchartsMethod(chart, 'setOption', options)
        
        // 添加窗口大小改变事件监听
        const resizeHandler = () => safeEchartsMethod(chart, 'resize')
        window.addEventListener('resize', resizeHandler)
        
        // 添加清理方法
        chart._cleanup = () => {
          window.removeEventListener('resize', resizeHandler)
          safeEchartsMethod(chart, 'dispose')
        }
        
        return chart
      } catch (e) {
        console.error('图表渲染失败:', e)
        if (retries > 0) {
          setTimeout(() => {
            app.config.globalProperties.$ensureChartRender(chartRef, options, retries - 1)
          }, 200)
        }
        return null
      }
    }
    
    // 提供一个重绘所有图表的方法
    app.config.globalProperties.$resizeAllCharts = () => {
      try {
        if (echarts && typeof echarts.getInstanceByDom === 'function') {
          const instances = echarts.getInstanceByDom
          if (instances) {
            Object.keys(instances).forEach(key => {
              const instance = instances[key]
              if (instance && typeof instance.resize === 'function') {
                try {
                  instance.resize()
                } catch (e) {
                  console.warn(`调整图表大小失败:`, e)
                }
              }
            })
          }
        }
      } catch (e) {
        console.warn('重绘所有图表失败:', e)
      }
    }
    
    // 添加全局指令，用于安全地初始化图表
    app.directive('safe-chart', {
      mounted(el, binding) {
        try {
          const chart = echarts.init(el)
          if (binding.value) {
            safeEchartsMethod(chart, 'setOption', binding.value)
          }
          el.__chart__ = chart
        } catch (e) {
          console.warn('v-safe-chart初始化失败:', e)
        }
      },
      updated(el, binding) {
        try {
          const chart = el.__chart__
          if (chart && binding.value) {
            safeEchartsMethod(chart, 'setOption', binding.value)
          }
        } catch (e) {
          console.warn('v-safe-chart更新失败:', e)
        }
      },
      unmounted(el) {
        try {
          const chart = el.__chart__
          if (chart) {
            safeEchartsMethod(chart, 'dispose')
          }
        } catch (e) {
          console.warn('v-safe-chart卸载失败:', e)
        }
      }
    })
  }
}

// 延迟加载非关键资源
const lazyLoadNonCriticalResources = () => {
  // 延迟加载统计脚本、字体等非关键资源
  setTimeout(() => {
    preloadResources()
  }, 1000)
}

// 初始化Pinia
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// 创建Vue应用
const app = createApp(App)

// 性能优化：使用异步组件和路由预加载
router.beforeEach((to, from, next) => {
  // 显示进度指示器或加载状态
  document.body.classList.add('page-loading')
  
  // 预加载下一个页面的组件
  if (to.matched.length > 0) {
    to.matched.forEach(record => {
      if (typeof record.components.default === 'function') {
        record.components.default()
      }
    })
  }
  
  next()
})

router.afterEach(() => {
  // 延迟移除加载状态，使过渡更平滑
  setTimeout(() => {
    document.body.classList.remove('page-loading')
  }, 100)
})

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  size: 'default'
})

// 注册所有图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册echarts插件
app.use(echartsPlugin)
app.component('v-chart', VChart)

// 应用启动
app.mount('#app')

// 记录性能指标
console.log(`应用加载完成，用时: ${Date.now() - loadTime}ms`)

// 延迟加载非关键资源
lazyLoadNonCriticalResources() 