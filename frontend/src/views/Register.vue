<!-- AIMETA P=注册页_用户注册|R=注册表单|NR=不含登录功能|E=route:/register#component:Register|X=ui|A=注册表单|D=vue|S=dom,net|RD=./README.ai -->
<template>
  <div class="register-container">
    <!-- Decorative background elements -->
    <div class="register-bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <!-- Logo / Title -->
    <div class="mb-8">
      <TypewriterEffect text="拯 救 小 说 家" />
    </div>

    <!-- Book-style Register Card -->
    <div v-if="allowRegistration" class="register-card">
      <!-- Book spine decoration -->
      <div class="book-spine"></div>

      <!-- Card content -->
      <div class="register-card-content">
        <!-- Header with decorative line -->
        <div class="text-center mb-6">
          <div class="register-ornament mb-4">
            <span class="ornament-line"></span>
            <svg class="ornament-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14l9-5-9-5-9 5 9 5z" />
              <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
            </svg>
            <span class="ornament-line"></span>
          </div>
          <h2 class="novel-headline text-center">
            加入我们
          </h2>
          <p class="novel-label mt-2">
            开启您的创作新篇章
          </p>
        </div>

        <!-- Register Form -->
        <form @submit.prevent="handleRegister" class="space-y-4">
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

          <!-- Email Field -->
          <div class="novel-field">
            <label for="email" class="novel-field-label">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              邮箱
            </label>
            <input
              v-model="email"
              id="email"
              name="email"
              type="email"
              required
              class="novel-input novel-input-writing"
              placeholder="请输入邮箱"
            />
          </div>

          <!-- Verification Code Field -->
          <div class="novel-field">
            <label for="verificationCode" class="novel-field-label">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              验证码
            </label>
            <div class="flex gap-3 items-center">
              <input
                v-model="verificationCode"
                id="verificationCode"
                name="verificationCode"
                type="text"
                required
                class="novel-input novel-input-writing flex-1"
                placeholder="请输入验证码"
              />
              <button
                type="button"
                @click="sendCode"
                :disabled="countdown > 0 || sending"
                class="send-code-btn"
              >
                <span v-if="sending">发送中...</span>
                <span v-else>{{ countdown > 0 ? countdown + 's' : '发送验证码' }}</span>
              </button>
            </div>
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
              placeholder="请输入密码（至少8位）"
            />
          </div>

          <!-- Error Message -->
          <div v-if="error" class="register-message register-error">
            <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ error }}</span>
          </div>

          <!-- Success Message -->
          <div v-if="success" class="register-message register-success">
            <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ success }}</span>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="register-submit-btn"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
            <span>创建账户</span>
          </button>
        </form>

        <!-- Login Link -->
        <p class="mt-6 text-center novel-label">
          已有账户？
          <router-link to="/login" class="register-login-link">
            立即登录
          </router-link>
        </p>
      </div>
    </div>

    <!-- Registration Closed Card -->
    <div v-else class="register-card register-closed-card">
      <div class="book-spine"></div>
      <div class="register-card-content text-center">
        <div class="register-ornament mb-4">
          <span class="ornament-line"></span>
          <svg class="ornament-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span class="ornament-line"></span>
        </div>
        <h2 class="novel-headline mb-4">暂未开放注册</h2>
        <p class="novel-label mb-6">请联系管理员或稍后再试</p>
        <router-link to="/login" class="register-back-btn">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回登录
        </router-link>
      </div>
    </div>

    <!-- Footer -->
    <p class="register-footer">
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
const email = ref('');
const verificationCode = ref('');
const password = ref('');
const countdown = ref(0);
const sending = ref(false);
const error = ref('');
const success = ref('');
const router = useRouter();
const authStore = useAuthStore();
const allowRegistration = computed(() => authStore.allowRegistration);

// 进入页面即拉取认证开关，避免展示无效注册表单
onMounted(async () => {
  try {
    await authStore.fetchAuthOptions();
  } catch (error) {
    console.error('加载认证开关失败', error);
  }
  if (!allowRegistration.value) {
    success.value = '';
    error.value = '当前已关闭注册，请稍后再试。';
  }
});

const validateInput = () => {
  // Password validation
  if (password.value.length < 8) {
    return '密码必须至少8个字符';
  }

  // Username validation
  const usernameVal = username.value;
  const hasChinese = /[\u4e00-\u9fa5]/.test(usernameVal);
  const isNumeric = /^\d+$/.test(usernameVal);
  const isAlphanumeric = /^[a-zA-Z0-9]+$/.test(usernameVal);

  if (isNumeric) {
    return '用户名不能是纯数字';
  }

  if (hasChinese && usernameVal.length <= 1) {
    return '户名长度必须大于2个汉字';
  }

  if (isAlphanumeric && !hasChinese && usernameVal.length <= 6) {
    return '用户名长度必须大于6个字母或数字';
  }

  return null;
};

const sendCode = async () => {
  error.value = '';
  success.value = '';

  if (!allowRegistration.value) {
    error.value = '当前已关闭注册，请联系管理员。';
    return;
  }

  if (!email.value) {
    error.value = '请输入邮箱';
    return;
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email.value)) {
    error.value = '邮箱格式不正确';
    return;
  }

  sending.value = true;
  try {
    const res = await fetch(`/api/auth/send-code?email=${encodeURIComponent(email.value)}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const errMsg = await res.json();
      throw new Error(errMsg.detail || '发送验证码失败');
    }
    success.value = '验证码已发送，请查收邮箱';
    countdown.value = 60;
    const timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) clearInterval(timer);
    }, 1000);
  } catch (err: any) {
    error.value = err.message;
  } finally {
    sending.value = false;
  }
};

const handleRegister = async () => {
  error.value = '';
  success.value = '';

  const validationError = validateInput();
  if (validationError) {
    error.value = validationError;
    return;
  }

  if (!allowRegistration.value) {
    error.value = '当前已关闭注册，请联系管理员。';
    return;
  }

  try {
    const res = await fetch('/api/auth/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        email: email.value,
        password: password.value,
        verification_code: verificationCode.value
      })
    });
    if (!res.ok) {
      const errMsg = await res.json();
      throw new Error(errMsg.detail || '注册失败');
    }
    success.value = '注册成功！正在跳转到登录页面...';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } catch (err: any) {
    error.value = err.message || '注册失败，请稍后再试。';
    console.error(err);
  }
};
</script>

<style scoped>
.register-container {
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
.register-bg-decoration {
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
  background: radial-gradient(circle, var(--novel-secondary-container) 0%, transparent 70%);
  top: -100px;
  left: -100px;
}

.bg-circle-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, var(--novel-primary-container) 0%, transparent 70%);
  bottom: -50px;
  right: -50px;
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, var(--novel-tertiary-container) 0%, transparent 70%);
  top: 40%;
  right: 15%;
}

/* Register Card - Book style */
.register-card {
  position: relative;
  width: 100%;
  max-width: 440px;
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

.register-card-content {
  padding: var(--novel-space-6);
  padding-left: calc(var(--novel-space-6) + 16px);
  position: relative;
}

/* Decorative paper texture overlay */
.register-card-content::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--novel-paper-texture);
  pointer-events: none;
  opacity: 0.5;
}

/* Ornament */
.register-ornament {
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

/* Send code button */
.send-code-btn {
  flex-shrink: 0;
  padding: 0 var(--novel-space-4);
  height: 52px;
  background: var(--novel-secondary);
  color: var(--novel-on-secondary);
  border: none;
  border-radius: var(--novel-radius-md);
  font-size: var(--novel-text-caption);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
  white-space: nowrap;
}

.send-code-btn:hover:not(:disabled) {
  background: var(--novel-secondary-dark);
}

.send-code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Messages */
.register-message {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-3);
  border-radius: var(--novel-radius-md);
  font-size: var(--novel-text-label);
}

.register-error {
  background-color: var(--novel-error-container);
  color: var(--novel-on-error-container);
}

.register-success {
  background-color: var(--novel-success-container);
  color: var(--novel-on-success-container);
}

/* Submit button */
.register-submit-btn {
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

.register-submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--novel-shadow-lg);
}

.register-submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

/* Login link */
.register-login-link {
  color: var(--novel-primary);
  font-weight: 600;
  text-decoration: none;
  transition: color var(--novel-duration-fast);
}

.register-login-link:hover {
  color: var(--novel-primary-dark);
  text-decoration: underline;
}

/* Back button for closed registration */
.register-back-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--novel-space-2);
  padding: var(--novel-space-3) var(--novel-space-6);
  color: var(--novel-primary);
  font-weight: 500;
  text-decoration: none;
  border: 1.5px solid var(--novel-outline);
  border-radius: var(--novel-radius-md);
  transition: all var(--novel-duration-fast) var(--novel-easing-standard);
}

.register-back-btn:hover {
  background: var(--novel-primary-container);
  border-color: var(--novel-primary);
}

/* Footer */
.register-footer {
  display: flex;
  align-items: center;
  gap: var(--novel-space-2);
  margin-top: var(--novel-space-8);
  color: var(--novel-on-surface-variant);
  font-size: var(--novel-text-caption);
}

/* Responsive */
@media (max-width: 480px) {
  .register-card-content {
    padding: var(--novel-space-5);
    padding-left: calc(var(--novel-space-5) + 12px);
  }

  .book-spine {
    width: 12px;
  }

  .send-code-btn {
    padding: 0 var(--novel-space-3);
    font-size: 11px;
  }
}
</style>
