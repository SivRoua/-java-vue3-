const { test } = require('node:test')
const assert = require('node:assert/strict')
const vm = require('node:vm')
const { readFileSync } = require('node:fs')
const { resolve } = require('node:path')
const { defineStore, createPinia, setActivePinia } = require('pinia')
async function load(file, imports, globals = {}) {
  const context = vm.createContext({ console, Blob, ...globals })
  const module = new vm.SourceTextModule(readFileSync(resolve(__dirname, '../src', file), 'utf8'), {
    context, initializeImportMeta: meta => { meta.env = { DEV: false } }
  })
  await module.link(name => {
    const values = imports[name]
    if (!values) throw Error('Unexpected import: ' + name)
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [key, value] of Object.entries(values)) this.setExport(key, value)
    }, { context })
  })
  await module.evaluate()
  return module.namespace
}
test('paginated responses retain metadata while ordinary lists remain arrays', async () => {
  let processResponse
  const service = { interceptors: { request: { use() {} }, response: { use(fn) { processResponse = fn } } } }
  await load('utils/request.js', { axios: { default: { create: () => service } }, 'element-plus': { ElMessage: {} }, '@/store/user': { useUserStore() {} }, '@/router': { default: {} } })
  const payload = { data: [{ id: 1 }], meta: { total: 123 } }
  assert.equal(processResponse({ data: payload, config: {} }).meta.total, 123)
  assert.deepEqual(processResponse({ data: { data: [1, 2] }, config: {} }), [1, 2])
})
test('inactive user creation preserves the selected activation flag', async () => {
  let sent
  const api = await load('api/user.js', { '@/utils/request': { default: async config => { sent = config.data } }, '@/config/api': { API_ENDPOINTS: {} } }, { localStorage: { getItem: () => 'test' } })
  await api.createUser({ is_active: false })
  assert.equal(sent.is_active, false)
  await api.createUser({ is_active: true })
  assert.equal(sent.is_active, true)
})
test('freshness expires without another HTTP response and retains sampling time', async () => {
  setActivePinia(createPinia())
  let now = 100000, clock, cleared = false
  class Clock extends Date { static now() { return now } }
  const api = await load('store/monitor.js', { pinia: { defineStore }, '@/api/monitor': { getSensorData: async () => ({ data: { air_temperature: 25 }, timestamp: new Date(100000).toISOString(), source: 'realtime' }) }, 'element-plus': { ElMessage: {} } }, { Date: Clock, setInterval: fn => { clock = fn; return 1 }, clearInterval: () => { cleared = true } })
  const store = api.useMonitorStore()
  await store.fetchRealTimeData()
  store.startFreshnessClock()
  assert.equal(store.isFresh, true)
  now += 20000; clock()
  assert.equal(store.isFresh, false)
  assert.equal(store.lastUpdateTime, new Date(100000).toISOString())
  store.stopRealTimeUpdate()
  assert.equal(cleared, true)
})
