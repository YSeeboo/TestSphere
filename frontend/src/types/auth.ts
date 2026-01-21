/**
 * 认证相关的 TypeScript 类型定义
 */

/**
 * Token 响应接口
 */
export interface TokenResponse {
  access_token: string
  token_type: string
  refresh_token?: string
}

/**
 * Token Payload 接口
 */
export interface TokenPayload {
  sub?: number // 用户ID
  exp?: number // 过期时间戳
  iat?: number // 签发时间戳
}
