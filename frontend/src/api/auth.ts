/**
 * 认证相关的 API 调用函数
 */

import request from '@/utils/request'
import type { TokenResponse } from '@/types/auth'
import type { UserInfo, UserLoginForm, UserRegisterForm } from '@/types/user'

/**
 * 用户登录 API
 * @param loginForm 登录表单数据
 * @returns Token 响应
 */
export function login(loginForm: UserLoginForm): Promise<TokenResponse> {
  return request.post<TokenResponse>('/auth/login-json', {
    email: loginForm.email,
    password: loginForm.password,
  })
}

/**
 * 用户注册 API
 * @param registerForm 注册表单数据
 * @returns 用户信息
 */
export function register(registerForm: UserRegisterForm): Promise<UserInfo> {
  return request.post<UserInfo>('/auth/register', registerForm)
}

/**
 * 获取当前用户信息 API
 * @returns 当前用户信息
 */
export function getMe(): Promise<UserInfo> {
  return request.get<UserInfo>('/users/me')
}

/**
 * 更新当前用户信息 API
 * @param updateData 更新数据
 * @returns 更新后的用户信息
 */
export function updateMe(updateData: { username?: string; password?: string }): Promise<UserInfo> {
  return request.put<UserInfo>('/users/me', updateData)
}
