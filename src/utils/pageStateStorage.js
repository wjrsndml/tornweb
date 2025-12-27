// pageStateStorage.js
// 作用：在浏览器 localStorage 中持久化“上次使用的功能页/菜单”，用于刷新/重新打开后自动恢复到上一次页面。
// 说明：
// - 仅在用户浏览器本地保存，不会上传到服务器。
// - 写入/读取 localStorage 失败时会在控制台输出错误，但不会影响页面正常使用。

const STORAGE_KEYS = {
  lastActiveMenu: 'tornweb.lastActiveMenu'
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
    console.error('[pageStateStorage] 读取 localStorage 失败：', e)
    return null
  }
}

const writeRaw = (key, value) => {
  if (!hasLocalStorage()) return
  try {
    window.localStorage.setItem(key, value)
  } catch (e) {
    console.error('[pageStateStorage] 写入 localStorage 失败：', e)
  }
}

const removeRaw = (key) => {
  if (!hasLocalStorage()) return
  try {
    window.localStorage.removeItem(key)
  } catch (e) {
    console.error('[pageStateStorage] 删除 localStorage 失败：', e)
  }
}

export function getStoredActiveMenu(defaultValue = 'split') {
  const raw = readRaw(STORAGE_KEYS.lastActiveMenu)
  const v = String(raw || '').trim()
  return v || String(defaultValue || 'split')
}

export function setStoredActiveMenu(menu) {
  const v = String(menu || '').trim()
  if (!v) {
    removeRaw(STORAGE_KEYS.lastActiveMenu)
    return
  }
  writeRaw(STORAGE_KEYS.lastActiveMenu, v)
}

export function clearStoredActiveMenu() {
  removeRaw(STORAGE_KEYS.lastActiveMenu)
}


