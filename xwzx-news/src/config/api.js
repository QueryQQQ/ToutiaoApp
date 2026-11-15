/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL（新闻/用户/收藏/历史等业务接口都靠它拼地址，不要改成 DeepSeek）
  baseURL: 'http://127.0.0.1:8000',
}

// AI 问答功能配置
// ⚠️ 当前为「前端直连 DeepSeek」的本地调试方案，apiKey 会打包进浏览器代码。
// 正式上线前请改为走后端代理：chatEndpoint = `${apiConfig.baseURL}/api/ai/chat`
export const aiChatConfig = {
  // DeepSeek 对话接口
  chatEndpoint: 'https://api.deepseek.com/chat/completions',

  // API Key 从环境变量读取，真实值放在 xwzx-news/.env.local（已被 .gitignore 忽略）
  // 缺失时为空字符串，请求会返回 401，不会把密钥带进仓库
  apiKey: import.meta.env.VITE_DEEPSEEK_API_KEY || '',

  // 模型名
  model: 'deepseek-flash',

  // 思考模式：disabled 才会立刻出字；enabled 会先返回 reasoning_content
  thinking: 'disabled',

  // 是否使用流式输出
  useStream: true,
}
