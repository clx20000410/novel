<!-- AIMETA P=登录页_用户登录|R=登录表单_认证|NR=不含注册功能|E=route:/login#component:Login|X=ui|A=登录表单|D=vue|S=dom,net,storage|RD=./README.ai -->
<template>
  <div class="login-container">
    <!-- Decorative background elements -->
    <div class="login-bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <!-- Logo / Title -->
    <div class="mb-8">
      <TypewriterEffect text="拯 救 小 说 家" />
    </div>

    <!-- Book-style Login Card -->
    <div class="login-card">
      <!-- Book spine decoration -->
      <div class="book-spine"></div>

      <!-- Card content -->
      <div class="login-card-content">
        <!-- Header with decorative line -->
        <div class="text-center mb-8">
          <div class="login-ornament mb-4">
            <span class="ornament-line"></span>
            <svg class="ornament-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span class="ornament-line"></span>
          </div>
          <h2 class="novel-headline text-center">
            欢迎回来
          </h2>
          <p class="novel-label mt-2">
            登录以继续您的创作之旅
          </p>
        </div>

        <!-- Login Form -->
        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Username Field -->
          <div class="novel-field">
            <label for="username" class="novel-field-label">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              用户名
            </label>
            <input
              v-model="username"
              id="username"
              name="username"
              type="text"
              required
              class="novel-input novel-input-writing"
              placeholder="请输入用户名"
            />
          </div>

          <!-- Password Field -->
          <div class="novel-field">
            <label for="password" class="novel-field-label">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              密码
            </label>
            <input
              v-model="password"
              id="password"
              name="password"
              type="password"
              required
              class="novel-input novel-input-writing"
              placeholder="请输入密码"
            />
          </div>

          <!-- Error Message -->
          <div v-if="error" class="login-error">
            <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ error }}</span>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="isLoading"
            class="login-submit-btn"
          >
            <svg v-if="isLoading" class="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span>{{ isLoading ? '正在登录...' : '开始创作' }}</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="novel-divider-ornament my-6">
          <span class="novel-caption">或</span>
        </div>

        <!-- Linux DO Login -->
        <div v-if="enableLinuxdoLogin">
          <a
            href="/api/auth/linuxdo/login"
            class="login-social-btn"
          >
            <svg class="w-5 h-5" aria-hidden="true" viewBox="0 0 496 512">
              <path fill="currentColor" d="M248 8C111 8 0 119 0 256s111 248 248 248 248-111 248-248S385 8 248 8zm0 448c-110.5 0-200-89.5-200-200S137.5 56 248 56s200 89.5 200 200-89.5 200-200 200z"></path>
            </svg>
            使用 Linux DO 登录
          </a>
        </div>

        <!-- Register Link -->
        <p v-if="allowRegistration" class="mt-6 text-center novel-label">
          还没有账户？
          <router-link to="/register" class="login-register-link">
            立即注册
          </router-link>
        </p>
      </div>
    </div>

    <!-- Footer -->
    <p class="login-footer">
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
      Powered by AI · 文学优雅设计
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import TypewriterEffect from '@/components/TypewriterEffect.vue';

const username = ref('');
const password = ref('');
const error = ref('');
const isLoading = ref(false);
const router = useRouter();
const authStore = useAuthStore();
const allowRegistration = computed(() => authStore.allowRegistration);
const enableLinuxdoLogin = computed(() => authStore.enableLinuxdoLogin);

// 首屏自动拉取认证配置，确保登录页动态展示开关
onMounted(() => {
  authStore.fetchAuthOptions().catch((error) => {
    console.error('初始化认证配置失败', error);
  });
});

const handleLogin = async () => {
  error.value = '';
  isLoading.value = true;
  try {
    const mustChange = await authStore.login(username.value, password.value);
    const user = authStore.user;
    if (user?.is_admin && (authStore.mustChangePassword || mustChange)) {
      router.push({ name: 'admin', query: { tab: 'password' } });
    } else {
      router.push('/');
    }
  } catch (err) {
    error.value = '登录失败，请检查您的用户名和密码。';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--novel-space-6);
  background: var(--novel-surface-dim);
  position: relative;
  overflow: hidden;
}

/* Background decorations */
.login-bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
}

.bg-circle-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, var(--novel-primary-container) 0%, transparent 70%);
  top: -100px;
  right: -100px;
}

.bg-circle-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, var(--novel-secondary-container) 0%, transparent 70%);
  bottom: -50px;
  left: -50px;
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--novel-tertiary-container) 0%, transparent 70%);
  top: 50%;
  left: 10%;
}

/* Login Card - Book style */
.login-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--novel-surface);
  border-radius: var(--novel-radius-xl);
  box-shadow: var(--novel-shadow-lg);
  overflow: hidden;
  animation: card-appear 0.6s var(--novel-easing-emphasized);
}

@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Book spine */
.book-spine {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 16px;
  background: var(--novel-book-spine);
  box-shadow: inset -3px 0 6px rgba(0, 0, 0, 0.15);
}

.login-card-content {
  padding: var(--novel-space-8);
  padding-left: calc(var(--novel-space-8) + 16px);
  position: relative;
}

/* Decorative paper texture overlay */
.login-card-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  pointer-events: none;
  opacity: 0.5;
}

/* Ornament */
.login-ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-3);
  color: var(--novel-primary);
}

.ornament-line {
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--novel-primary), transparent);
}

.ornament-icon {
  width: 28px;
  height: 28px;
}

/* Form field */
.novel-field {
  position: relative;
}

.novel-field-label {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  font-size: var(--novel-text-caption);
  font-weight: 500;
  color: var(--novel-on-surface-variant);
  margin-bottom: var(--novel-space-2);
}

/* Error message */
.login-error {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-3);
  border-radius: var(--novel-radius-md);
  background-color: var(--novel-error-container);
  color: var(--novel-on-error-container);
  font-size: var(--novel-text-label);
}

/* Submit button */
.login-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-2);
  width: 100%;
  height: 52px;
  margin-top: var(--novel-space-4);
  padding: 0 var(--novel-space-6);
  background: var(--novel-book-spine);
  color: var(--novel-on-primary);
  border: none;
  border-radius: var(--novel-radius-md);
  font-family: var(--novel-font-body);
  font-size: var(--novel-text-body);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--novel-duration-normal) var(--novel-easing-standard);
  box-shadow: var(--novel-shadow-md);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.login-submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--novel-shadow-lg);
}

.login-submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Social login button */
.login-social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--novel-space-2);
  width: 100%;
  height: 48px;
  padding: 0 var(--novel-space-6);
  background: var(--novel-surface);
  color: var(--novel-on-surface);
  border: 1.5px solid var(--novel-outline);
  border-radius: var(--novel-radius-md);
  font-size: var(--novel-text-label);
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.login-social-btn:hover {
  background: var(--novel-surface-container);
  border-color: var(--novel-primary);
  color: var(--novel-primary);
}

/* Register link */
.login-register-link {
  color: var(--novel-primary);
  font-weight: 600;
  text-decoration: none;
  transition: color var(--novel-duration-fast);
}

.login-register-link:hover {
  color: var(--novel-primary-dark);
  text-decoration: underline;
}

/* Footer */
.login-footer {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  margin-top: var(--novel-space-8);
  color: var(--novel-on-surface-variant);
  font-size: var(--novel-text-caption);
}

/* Responsive */
@media (max-width: 480px) {
  .login-card-content {
    padding: var(--novel-space-6);
    padding-left: calc(var(--novel-space-6) + 12px);
  }

  .book-spine {
    width: 12px;
  }
}
</style>
