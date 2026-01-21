/**
 * 用户相关的 TypeScript 类型定义
 */

/**
 * 用户信息接口
 */
export interface UserInfo {
  id: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
}

/**
 * 用户注册表单
 */
export interface UserRegisterForm {
  email: string
  username: string
  password: string
}

/**
 * 用户登录表单
 */
export interface UserLoginForm {
  email: string
  password: string
}

/**
 * 用户更新表单
 */
export interface UserUpdateForm {
  username?: string
  password?: string
}
