<script setup lang="ts">
/**
 * 登录页面
 * 包含 Email 和 Password 表单验证
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'
import type { UserLoginForm } from '@/types/user'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 登录表单数据
const loginForm = reactive<UserLoginForm>({
  email: '',
  password: '',
})

// 表单验证规则
const rules: FormRules = {
  email: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
}

const loading = ref(false)

/**
 * 处理登录
 */
async function handleLogin() {
  if (!loginFormRef.value) return
  
  // 表单验证
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.login(loginForm)
      // 登录成功后会在 store 中自动跳转到 dashboard
    } catch (error) {
      console.error('登录失败:', error)
    } finally {
      loading.value = false
    }
  })
}

/**
 * 跳转到注册页
 */
function goToRegister() {
  router.push('/register')
}
</script>

<template>
  <div class="login-container">
    <!-- 左侧展示区域 -->
    <div class="left-section">
      <!-- 3D 插图占位符 -->
      <div class="illustration">
        <div class="illustration-placeholder">
          <div class="placeholder-icon">🎨</div>
          <p>3D 插图占位符</p>
          <p class="placeholder-hint">请上传 3D 插图图片</p>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单区域 -->
    <div class="right-section">
      <div class="login-card">
        <!-- Logo 和标题 -->
        <div class="login-header">
          <div class="logo-container">
            <div class="logo-placeholder">
              <span class="logo-icon">🎯</span>
            </div>
            <h1 class="app-title">TestSphere</h1>
          </div>
          <p class="app-subtitle">开源持续测试工具</p>
        </div>

        <!-- 账号登录标题 -->
        <div class="form-title">
          <h2>账号登录</h2>
        </div>

        <!-- 登录表单 -->
        <el-form 
          ref="loginFormRef"
          :model="loginForm" 
          :rules="rules"
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="email">
            <el-input 
              v-model="loginForm.email" 
              type="text" 
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="请输入密码" 
              size="large"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              :loading="loading" 
              size="large"
              class="login-button"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部链接 -->
        <div class="login-footer">
          <el-link type="primary" @click="goToRegister">还没有账号？立即注册</el-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.login-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
  overflow: hidden;
}

// 左侧展示区域
.left-section {
  flex: 1;
  background: linear-gradient(135deg, #e8e5f5 0%, #f0eef8 50%, #f5f3fa 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;

  .illustration {
    width: 100%;
    max-width: 600px;
    display: flex;
    align-items: center;
    justify-content: center;

    .illustration-placeholder {
      width: 500px;
      height: 500px;
      background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
      border-radius: 20px;
      border: 2px dashed rgba(139, 92, 246, 0.3);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      transition: all 0.3s ease;

      &:hover {
        border-color: rgba(139, 92, 246, 0.5);
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%);
      }

      .placeholder-icon {
        font-size: 80px;
      }

      p {
        margin: 0;
        color: #8b5cf6;
        font-size: 18px;
        font-weight: 500;
      }

      .placeholder-hint {
        font-size: 14px;
        color: #a78bfa;
        font-weight: 400;
      }
    }
  }
}

// 右侧登录区域
.right-section {
  width: 480px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.05);
}

.login-card {
  width: 100%;
  max-width: 400px;

  .login-header {
    text-align: center;
    margin-bottom: 40px;

    .logo-container {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin-bottom: 12px;

      .logo-placeholder {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        border: 2px dashed rgba(255, 255, 255, 0.4);
        position: relative;

        .logo-icon {
          font-size: 28px;
          filter: grayscale(0.2);
        }
        
        &::after {
          content: 'Logo占位';
          position: absolute;
          bottom: -22px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 10px;
          color: #a78bfa;
          white-space: nowrap;
        }
      }

      .app-title {
        font-size: 32px;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
      }
    }

    .app-subtitle {
      font-size: 14px;
      color: #6b7280;
      margin: 0;
    }
  }

  .form-title {
    margin-bottom: 30px;

    h2 {
      font-size: 20px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
    }
  }

  .login-form {
    .el-form-item {
      margin-bottom: 24px;
    }

    .login-button {
      width: 100%;
      height: 44px;
      font-size: 16px;
      font-weight: 500;
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
      border: none;
      border-radius: 8px;
      transition: all 0.3s ease;

      &:hover {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
      }

      &:active {
        transform: translateY(0);
      }
    }
  }

  .login-footer {
    text-align: center;
    margin-top: 24px;
  }
}

// 自定义 input 样式
:deep(.el-input__wrapper) {
  border-radius: 8px;
  padding: 8px 15px;
  box-shadow: 0 0 0 1px #e5e7eb inset;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 0 0 1px #d1d5db inset;
  }

  &.is-focus {
    box-shadow: 0 0 0 1px #8b5cf6 inset;
  }
}

:deep(.el-input__inner) {
  font-size: 15px;
}

// 响应式设计
@media (max-width: 1024px) {
  .left-section {
    display: none;
  }

  .right-section {
    width: 100%;
  }
}
</style>
