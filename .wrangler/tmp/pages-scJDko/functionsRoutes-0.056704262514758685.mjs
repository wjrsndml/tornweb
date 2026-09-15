import { onRequestGet as __api_feishu_js_onRequestGet } from "E:\\code\\project\\tornweb\\functions\\api\\feishu.js"

export const routes = [
    {
      routePath: "/api/feishu",
      mountPath: "/api",
      method: "GET",
      middlewares: [],
      modules: [__api_feishu_js_onRequestGet],
    },
  ]