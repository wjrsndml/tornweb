// daguofan 飞书转发器（Cloudflare Pages Function 版，由 feishu.php 移植）
//
// 用途：手机 Torn PDA 的 GM_xmlhttpRequest 由原生 HTTP 客户端实现，请求之间不保存
// Cookie，而飞书共享表的游客会话要在多次 302 跳转中逐跳收发 Cookie，导致 PDA 上
// API 永远返回 code=5（Login Required）。本函数在服务器端维持游客会话（Cookie 表），
// 把白名单内的只读请求转发给飞书并原样返回，数据源仍是飞书共享表。
//
// 部署：随仓库 git push 自动部署，路由 functions/api/feishu.js -> /api/feishu。
// 安全：仅允许固定的 shareToken 和两个只读接口、白名单查询参数，不能当作通用代理。

const SHARE_TOKEN = 'shrcnGAYPu4vSyCNN3KVbz2FAmc';
const API_BASE = 'https://smth-torncity.feishu.cn/space/api/bitable/external/view/share/';
const SHARE_URL = 'https://smth-torncity.feishu.cn/share/base/view/' + SHARE_TOKEN;
const ALLOWED_ENDPOINTS = ['records_and_meta', 'records_by_page'];
const ALLOWED_PARAMS = ['removeFmlExtra', 'offset', 'offsetNum', 'limit', 'revToken'];
const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

// 每个 isolate 一份的游客会话 Cookie 表（替代 PHP 版 tmp 下的 cookie 文件）。
// isolate 被回收也没关系，下面 code=5 的重建逻辑会自动恢复会话。
const cookieJars = new Map();

function jarFor(token) {
	let jar = cookieJars.get(token);
	if (!jar) cookieJars.set(token, (jar = new Map()));
	return jar;
}

function storeCookies(jar, response) {
	const setCookies = response.headers.getSetCookie
		? response.headers.getSetCookie()
		: [response.headers.get('Set-Cookie')].filter(Boolean);
	for (const line of setCookies) {
		const pair = line.split(';', 1)[0];
		const eq = pair.indexOf('=');
		if (eq > 0) jar.set(pair.slice(0, eq).trim(), pair.slice(eq + 1).trim());
	}
}

function cookieHeader(jar) {
	return [...jar].map(([name, value]) => `${name}=${value}`).join('; ');
}

// 等价于 PHP 版的 CURLOPT_FOLLOWLOCATION + COOKIEFILE/COOKIEJAR：手动逐跳跟随
// 302 并收发 Cookie（fetch 的自动重定向做不到跨跳保存 Cookie）
async function feishuGet(url, jar) {
	for (let hops = 0; ; hops++) {
		const headers = { 'User-Agent': USER_AGENT, Accept: 'application/json' };
		const cookie = cookieHeader(jar);
		if (cookie) headers.Cookie = cookie;
		const response = await fetch(url, {
			headers,
			redirect: 'manual',
			signal: AbortSignal.timeout(25_000),
		});
		storeCookies(jar, response);
		const location = response.headers.get('Location');
		if (response.status >= 300 && response.status < 400 && location && hops < 10) {
			url = new URL(location, url).href;
			continue;
		}
		return await response.text();
	}
}

function respond(status, body) {
	return new Response(body, {
		status,
		headers: {
			'Content-Type': 'application/json; charset=utf-8',
			'Access-Control-Allow-Origin': '*',
		},
	});
}

export async function onRequestGet({ request }) {
	const url = new URL(request.url);
	const endpoint = url.searchParams.get('e') ?? '';
	if (!ALLOWED_ENDPOINTS.includes(endpoint) || url.searchParams.get('shareToken') !== SHARE_TOKEN) {
		return respond(403, '{"code":403,"msg":"forbidden","data":{}}');
	}

	const params = new URLSearchParams({ shareToken: SHARE_TOKEN });
	for (const key of ALLOWED_PARAMS) {
		const value = url.searchParams.get(key);
		if (value !== null && value.length <= 300) params.set(key, value);
	}
	const apiUrl = API_BASE + endpoint + '?' + params.toString();
	const jar = jarFor(SHARE_TOKEN);

	let body;
	try {
		body = await feishuGet(apiUrl, jar);
		let code = 5;
		try {
			code = JSON.parse(body).code ?? 5;
		} catch { /* 非 JSON 响应按会话失效处理 */ }
		if (code === 5) {
			// 游客会话失效或尚未建立：访问共享链接重建会话（Set-Cookie 写入 jar），再重试一次
			await feishuGet(SHARE_URL, jar);
			body = await feishuGet(apiUrl, jar);
		}
	} catch (err) {
		return respond(502, JSON.stringify({ code: 502, msg: 'upstream error: ' + (err?.message ?? err), data: {} }));
	}
	return respond(200, body);
}
