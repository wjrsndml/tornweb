// apiKeyStorage.js
// 作用：在浏览器 localStorage 中安全地持久化 Torn API Key（以及可选的多 Key 文本），用于“记住 API Key”功能。
// 说明：
// - 仅在用户浏览器本地保存，不会上传到服务器。
// - 出于安全考虑：当值为空/全空白时会自动清除对应存储项。

const STORAGE_KEYS = {
  rememberApiKey: 'tornweb.rememberApiKey',
  apiKey: 'tornweb.apiKey',
  apiKeysPool: 'tornweb.apiKeysPool'
}

const hasLocalStorage = () => {
  try {
    return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
  } catch {
    return false
  }
}

const readRaw = (key) => {
  if (!hasLocalStorage()) return null
  try {
    return window.localStorage.getItem(key)
  } catch (e) {
    console.error('[apiKeyStorage] 读取 localStorage 失败：', e)
    return null
  }
}

const writeRaw = (key, value) => {
  if (!hasLocalStorage()) return
  try {
    window.localStorage.setItem(key, value)
  } catch (e) {
    console.error('[apiKeyStorage] 写入 localStorage 失败：', e)
  }
}

const removeRaw = (key) => {
  if (!hasLocalStorage()) return
  try {
    window.localStorage.removeItem(key)
  } catch (e) {
    console.error('[apiKeyStorage] 删除 localStorage 失败：', e)
  }
}

export function getRememberApiKeyEnabled(defaultValue = true) {
  const raw = readRaw(STORAGE_KEYS.rememberApiKey)
  if (raw == null) return Boolean(defaultValue)
  return raw === '1'
}

export function setRememberApiKeyEnabled(enabled) {
  writeRaw(STORAGE_KEYS.rememberApiKey, enabled ? '1' : '0')
}

export function getStoredApiKey() {
  const raw = readRaw(STORAGE_KEYS.apiKey)
  return (raw || '').trim()
}

export function setStoredApiKey(apiKey) {
  const v = String(apiKey || '').trim()
  if (!v) {
    removeRaw(STORAGE_KEYS.apiKey)
    return
  }
  writeRaw(STORAGE_KEYS.apiKey, v)
}

export function clearStoredApiKey() {
  removeRaw(STORAGE_KEYS.apiKey)
}

export function getStoredApiKeysPool() {
  return readRaw(STORAGE_KEYS.apiKeysPool) || ''
}

export function setStoredApiKeysPool(text) {
  const v = String(text || '')
  if (!v.trim()) {
    removeRaw(STORAGE_KEYS.apiKeysPool)
    return
  }
  writeRaw(STORAGE_KEYS.apiKeysPool, v)
}

export function clearStoredApiKeysPool() {
  removeRaw(STORAGE_KEYS.apiKeysPool)
}


