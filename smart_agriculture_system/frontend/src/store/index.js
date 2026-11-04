import { createPinia } from 'pinia'
import { useMonitorStore } from './monitor'
import { useControlStore } from './control'

const pinia = createPinia()

export {
  pinia,
  useMonitorStore,
  useControlStore
}

export default pinia 