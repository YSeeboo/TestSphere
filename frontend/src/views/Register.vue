<script setup lang="ts">
/**
 * 注册页面
 * 包含 Email、Password 和确认密码的表单验证
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { register } from '@/api/auth'
import type { UserRegisterForm } from '@/types/user'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 注册表单数据（扩展字段）
interface RegisterFormData extends UserRegisterForm {
  confirmPassword: string
}

const registerForm = reactive<RegisterFormData>({
  email: '',
  username: '',
  password: '',
  confirmPassword: '',
})

/**
 * 验证确认密码
 */
const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] },
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const loading = ref(false)

/**
 * 处理注册
 */
async function handleRegister() {
  if (!registerFormRef.value) return
  
  // 表单验证
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      // 调用注册 API（不包含 confirmPassword）
      const { confirmPassword, ...registerData } = registerForm
      await register(registerData)
      
      // 注册成功后自动登录
      ElMessage.success('注册成功，正在自动登录...')
      
      // 使用注册时的邮箱和密码自动登录
      await userStore.login({
        email: registerData.email,
        password: registerData.password,
      })
      
      // 登录成功后会在 userStore.login() 中自动跳转到首页
    } catch (error: any) {
      console.error('注册或登录失败:', error)
      // 如果是注册失败，不做处理（API 会返回错误信息）
      // 如果是自动登录失败，提示用户手动登录
      if (error.message?.includes('登录')) {
        ElMessage.warning('自动登录失败，请手动登录')
        router.push('/login')
      }
    } finally {
      loading.value = false
    }
  })
}

/**
 * 跳转到登录页
 */
function goToLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2>用户注册</h2>
        </div>
      </template>
      
      <el-form 
        ref="registerFormRef"
        :model="registerForm" 
        :rules="rules"
        label-width="100px"
        @keyup.enter="handleRegister"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input 
            v-model="registerForm.email" 
            type="email" 
            placeholder="请输入邮箱"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="registerForm.username" 
            placeholder="请输入用户名"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="请输入密码" 
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="请再次输入密码" 
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading"
            style="width: 100%"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            style="width: 100%"
            @click="goToLogin"
          >
            已有账号，去登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 450px;
  
  .card-header {
    text-align: center;
    
    h2 {
      margin: 0;
      color: #303133;
    }
  }
}
</style>
