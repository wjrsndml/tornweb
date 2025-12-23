// requestRateLimiter.js
// 作用：提供一个简单的请求限速器（节流器），用于保证相邻两次请求之间至少间隔指定毫秒数（例如 1000ms=1秒）。
// 说明：
// - 该限速器适合串行 await 的请求场景（本项目抓取逻辑即为串行分页请求）。
// - 返回的 ensure() 在每次发请求前 await 一下即可。

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

export function createRateLimiter(minIntervalMs = 1000) {
  let lastRequestAt = 0

  return async function ensure() {
    const now = Date.now()
    const wait = Number(minIntervalMs) - (now - Number(lastRequestAt || 0))
    if (wait > 0) await sleep(wait)
    lastRequestAt = Date.now()
  }
}


