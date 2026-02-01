<!-- AIMETA P=LLM设置_模型配置界面|R=LLM多配置管理|NR=不含模型调用|E=component:LLMSettings|X=internal|A=设置组件|D=vue|S=dom,net|RD=./README.ai -->
<template>
  <div class="bg-white/70 backdrop-blur-xl rounded-2xl shadow-lg p-8">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-800">LLM 配置管理</h2>
        <p class="text-sm text-gray-500 mt-1">建议使用自己的中转 API 和 KEY</p>
      </div>
      <button
        @click="openCreateDialog"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        新增配置
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="flex justify-center items-center py-12">
      <svg class="animate-spin h-8 w-8 text-indigo-600" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>

    <!-- 空状态 -->
    <div v-else-if="configs.length === 0" class="text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <h3 class="mt-2 text-lg font-medium text-gray-900">暂无配置</h3>
      <p class="mt-1 text-sm text-gray-500">点击"新增配置"按钮创建您的第一个 LLM 配置</p>
    </div>

    <!-- 配置列表 -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="config in configs"
        :key="config.id"
        :class="[
          'relative bg-white rounded-xl border-2 p-5 transition-all cursor-pointer hover:shadow-md',
          config.is_active ? 'border-indigo-500 shadow-md' : 'border-gray-200 hover:border-gray-300'
        ]"
      >
        <!-- 激活标签 -->
        <div
          v-if="config.is_active"
          class="absolute -top-2 -right-2 bg-indigo-500 text-white text-xs font-semibold px-2 py-1 rounded-full"
        >
          当前使用
        </div>

        <!-- 配置信息 -->
        <div class="mb-4">
          <h3 class="text-lg font-semibold text-gray-800 truncate">{{ config.name }}</h3>
          <div class="mt-2 space-y-1 text-sm text-gray-500">
            <p class="truncate">
              <span class="font-medium">接口格式:</span>
              {{ getApiFormatLabel(config.api_format) }}
            </p>
            <p class="truncate" :title="config.llm_provider_url || '默认 URL'">
              <span class="font-medium">URL:</span>
              {{ config.llm_provider_url || '默认' }}
            </p>
            <p class="truncate">
              <span class="font-medium">模型:</span>
              {{ config.llm_provider_model || '默认' }}
            </p>
            <p class="truncate">
              <span class="font-medium">API Key:</span>
              {{ config.llm_provider_api_key ? maskApiKey(config.llm_provider_api_key) : '未设置' }}
            </p>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex gap-2 pt-3 border-t border-gray-100">
          <button
            v-if="!config.is_active"
            @click="handleActivate(config)"
            class="flex-1 px-3 py-1.5 text-sm bg-indigo-100 text-indigo-700 rounded-md hover:bg-indigo-200 transition-colors"
          >
            激活
          </button>
          <button
            @click="handleTestConnection(config)"
            :disabled="isTestingConnection === config.id"
            class="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed flex items-center gap-1"
          >
            <svg v-if="isTestingConnection === config.id" class="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ isTestingConnection === config.id ? '测试中...' : '测活' }}</span>
          </button>
          <button
            @click="openEditDialog(config)"
            class="flex-1 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            编辑
          </button>
          <button
            @click="handleDelete(config)"
            class="px-3 py-1.5 text-sm bg-red-100 text-red-600 rounded-md hover:bg-red-200 transition-colors"
          >
            删除
          </button>
        </div>

        <!-- 测活结果显示 -->
        <div
          v-if="connectionTestResults[config.id]"
          :class="[
            'mt-3 px-3 py-2 rounded-md text-sm flex items-center gap-2',
            connectionTestResults[config.id].success
              ? 'bg-green-50 text-green-700'
              : 'bg-red-50 text-red-700'
          ]"
        >
          <svg v-if="connectionTestResults[config.id].success" class="w-4 h-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="w-4 h-4 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <span class="flex-1 truncate">{{ connectionTestResults[config.id].message }}</span>
          <button
            @click="clearTestResult(config.id)"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div
      v-if="showDialog"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="closeDialog"
    >
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h3 class="text-xl font-bold text-gray-800 mb-6">
          {{ editingConfig ? '编辑配置' : '新增配置' }}
        </h3>
        <form @submit.prevent="handleSave" class="space-y-5">
          <!-- 配置名称 -->
          <div>
            <label for="name" class="block text-sm font-medium text-gray-700">配置名称</label>
            <input
              type="text"
              id="name"
              v-model="formData.name"
              required
              maxlength="64"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="例如：DeepSeek、Claude..."
            >
          </div>

          <!-- 接口格式 -->
          <div>
            <label for="api_format" class="block text-sm font-medium text-gray-700">接口格式</label>
            <select
              id="api_format"
              v-model="formData.api_format"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option v-for="option in API_FORMAT_OPTIONS" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <p class="mt-1 text-xs text-gray-500">
              {{ getApiFormatDescription(formData.api_format) }}
            </p>
          </div>

          <!-- API URL -->
          <div>
            <label for="url" class="block text-sm font-medium text-gray-700">API URL</label>
            <div class="relative mt-1">
              <input
                type="text"
                id="url"
                v-model="formData.llm_provider_url"
                class="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                :placeholder="getApiUrlPlaceholder(formData.api_format)"
              >
              <button
                type="button"
                @click="formData.llm_provider_url = ''"
                class="absolute inset-y-0 right-2 flex items-center px-2 text-gray-400 hover:text-gray-600"
              >
                <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          <!-- API Key -->
          <div>
            <label for="key" class="block text-sm font-medium text-gray-700">API Key</label>
            <div class="relative mt-1">
              <input
                :type="showApiKey ? 'text' : 'password'"
                id="key"
                v-model="formData.llm_provider_api_key"
                class="block w-full px-3 py-2 pr-20 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="留空则使用系统默认 Key"
              >
              <div class="absolute inset-y-0 right-2 flex items-center gap-1">
                <button
                  type="button"
                  @click="showApiKey = !showApiKey"
                  class="p-1 text-gray-400 hover:text-gray-600"
                >
                  <svg v-if="showApiKey" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd" />
                    <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                  </svg>
                  <svg v-else class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" />
                  </svg>
                </button>
                <button
                  type="button"
                  @click="formData.llm_provider_api_key = ''"
                  class="p-1 text-gray-400 hover:text-gray-600"
                >
                  <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 模型选择 -->
          <div>
            <label for="model" class="block text-sm font-medium text-gray-700">Model</label>
            <p class="text-xs text-gray-500 mt-0.5 mb-1">可直接输入自定义模型名称，或点击「获取模型」从列表选择</p>
            <div class="flex gap-2">
              <div class="relative flex-1">
                <input
                  type="text"
                  id="model"
                  v-model="formData.llm_provider_model"
                  @focus="onModelInputFocus"
                  @blur="hideDropdown"
                  class="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="输入模型名称，如 gpt-4o、claude-3-5-sonnet..."
                >
                <button
                  type="button"
                  @click="formData.llm_provider_model = ''"
                  class="absolute inset-y-0 right-2 flex items-center px-2 text-gray-400 hover:text-gray-600"
                >
                  <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
                <!-- 模型下拉列表 -->
                <div
                  v-if="showModelDropdown && availableModels.length > 0"
                  class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
                >
                  <div class="px-3 py-2 text-xs text-gray-400 border-b border-gray-100 bg-gray-50">
                    从列表选择或直接输入自定义名称
                  </div>
                  <div
                    v-for="model in filteredModels"
                    :key="model"
                    @mousedown="selectModel(model)"
                    class="px-3 py-2 cursor-pointer hover:bg-indigo-50 hover:text-indigo-600 text-sm"
                  >
                    {{ model }}
                  </div>
                  <div v-if="filteredModels.length === 0" class="px-3 py-2 text-sm text-gray-500">
                    无匹配模型，可继续输入自定义名称
                  </div>
                </div>
              </div>
              <button
                type="button"
                @click="loadModels"
                :disabled="isLoadingModels || !formData.llm_provider_api_key"
                class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <svg v-if="isLoadingModels" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ isLoadingModels ? '加载中...' : '获取模型' }}</span>
              </button>
            </div>
          </div>

          <!-- 蓝图生成每批章节数 -->
          <div>
            <label for="batchSize" class="block text-sm font-medium text-gray-700 mb-1">
              蓝图生成每批章节数
              <span class="text-xs text-gray-400 ml-1">（如果代理服务有输出限制，请减小此值）</span>
            </label>
            <input
              type="number"
              id="batchSize"
              v-model.number="formData.blueprint_batch_size"
              min="1"
              max="50"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="默认 5"
            >
          </div>

          <!-- 弹窗内测活按钮 -->
          <div class="pt-2">
            <button
              type="button"
              @click="handleTestConnectionInDialog"
              :disabled="isTestingConnectionInDialog || !formData.llm_provider_api_key || !formData.llm_provider_model"
              class="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <svg v-if="isTestingConnectionInDialog" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ isTestingConnectionInDialog ? '测试连接中...' : '测试连接' }}</span>
            </button>

            <!-- 弹窗内测活结果 -->
            <div
              v-if="dialogTestResult"
              :class="[
                'mt-2 px-3 py-2 rounded-md text-sm flex items-center gap-2',
                dialogTestResult.success
                  ? 'bg-green-50 text-green-700'
                  : 'bg-red-50 text-red-700'
              ]"
            >
              <svg v-if="dialogTestResult.success" class="w-4 h-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <svg v-else class="w-4 h-4 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
              <span>{{ dialogTestResult.message }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              @click="closeDialog"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              :disabled="isSaving"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-indigo-400 flex items-center gap-2"
            >
              <svg v-if="isSaving" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ isSaving ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import {
  getLLMConfigs,
  createLLMConfig,
  updateLLMConfig,
  deleteLLMConfig,
  activateLLMConfig,
  getAvailableModels,
  testLLMConnection,
  API_FORMAT_OPTIONS,
  type LLMConfig,
  type LLMConfigCreate,
  type LLMConfigUpdate,
  type ApiFormatType,
  type TestConnectionResponse,
} from '@/api/llm';

// 配置列表
const configs = ref<LLMConfig[]>([]);
const isLoading = ref(true);

// 弹窗状态
const showDialog = ref(false);
const editingConfig = ref<LLMConfig | null>(null);
const isSaving = ref(false);

// 表单数据
const formData = ref<LLMConfigCreate & { api_format: ApiFormatType }>({
  name: '',
  api_format: 'openai_chat',
  llm_provider_url: '',
  llm_provider_api_key: '',
  llm_provider_model: '',
  blueprint_batch_size: 5,
});

// API Key 显示状态
const showApiKey = ref(false);

// 模型列表
const availableModels = ref<string[]>([]);
const isLoadingModels = ref(false);
const showModelDropdown = ref(false);

// 连接测试
const isTestingConnection = ref<number | null>(null);
const connectionTestResults = ref<Record<number, TestConnectionResponse>>({});
const isTestingConnectionInDialog = ref(false);
const dialogTestResult = ref<TestConnectionResponse | null>(null);

// 根据输入过滤模型列表
const filteredModels = computed(() => {
  if (!formData.value.llm_provider_model) {
    return availableModels.value;
  }
  const searchTerm = formData.value.llm_provider_model.toLowerCase();
  return availableModels.value.filter(model =>
    model.toLowerCase().includes(searchTerm)
  );
});

// 加载配置列表
const loadConfigs = async () => {
  isLoading.value = true;
  try {
    configs.value = await getLLMConfigs();
  } catch (error) {
    console.error('加载配置列表失败:', error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(loadConfigs);

// 遮蔽 API Key
const maskApiKey = (key: string) => {
  if (key.length <= 8) {
    return '****';
  }
  return `${key.slice(0, 4)}...${key.slice(-4)}`;
};

// 获取 API 格式标签
const getApiFormatLabel = (format: ApiFormatType | string) => {
  const option = API_FORMAT_OPTIONS.find(opt => opt.value === format);
  return option?.label || format;
};

// 获取 API 格式描述
const getApiFormatDescription = (format: ApiFormatType) => {
  const option = API_FORMAT_OPTIONS.find(opt => opt.value === format);
  return option?.description || '';
};

// 获取 API URL 占位符
const getApiUrlPlaceholder = (format: ApiFormatType) => {
  const placeholders: Record<ApiFormatType, string> = {
    openai_chat: 'https://api.openai.com/v1',
    openai_responses: 'https://api.openai.com/v1',
    anthropic: 'https://api.anthropic.com',
    google: 'https://generativelanguage.googleapis.com/v1beta',
  };
  return placeholders[format] || 'https://api.example.com/v1';
};

// 打开创建弹窗
const openCreateDialog = () => {
  editingConfig.value = null;
  formData.value = {
    name: '',
    api_format: 'openai_chat',
    llm_provider_url: '',
    llm_provider_api_key: '',
    llm_provider_model: '',
    blueprint_batch_size: 5,
  };
  availableModels.value = [];
  showApiKey.value = false;
  dialogTestResult.value = null;
  showDialog.value = true;
};

// 打开编辑弹窗
const openEditDialog = (config: LLMConfig) => {
  editingConfig.value = config;
  formData.value = {
    name: config.name,
    api_format: config.api_format || 'openai_chat',
    llm_provider_url: config.llm_provider_url || '',
    llm_provider_api_key: config.llm_provider_api_key || '',
    llm_provider_model: config.llm_provider_model || '',
    blueprint_batch_size: config.blueprint_batch_size ?? 5,
  };
  availableModels.value = [];
  showApiKey.value = false;
  dialogTestResult.value = null;
  showDialog.value = true;
};

// 关闭弹窗
const closeDialog = () => {
  showDialog.value = false;
  editingConfig.value = null;
  dialogTestResult.value = null;
};

// 保存配置
const handleSave = async () => {
  if (!formData.value.name.trim()) {
    alert('请输入配置名称');
    return;
  }

  isSaving.value = true;
  try {
    if (editingConfig.value) {
      // 更新配置
      const updatePayload: LLMConfigUpdate = {};
      if (formData.value.name !== editingConfig.value.name) {
        updatePayload.name = formData.value.name;
      }
      if (formData.value.api_format !== (editingConfig.value.api_format || 'openai_chat')) {
        updatePayload.api_format = formData.value.api_format;
      }
      if (formData.value.llm_provider_url !== (editingConfig.value.llm_provider_url || '')) {
        updatePayload.llm_provider_url = formData.value.llm_provider_url || undefined;
      }
      if (formData.value.llm_provider_api_key !== (editingConfig.value.llm_provider_api_key || '')) {
        updatePayload.llm_provider_api_key = formData.value.llm_provider_api_key || undefined;
      }
      if (formData.value.llm_provider_model !== (editingConfig.value.llm_provider_model || '')) {
        updatePayload.llm_provider_model = formData.value.llm_provider_model || undefined;
      }
      await updateLLMConfig(editingConfig.value.id, updatePayload);
    } else {
      // 创建配置
      await createLLMConfig(formData.value);
    }
    await loadConfigs();
    closeDialog();
  } catch (error) {
    console.error('保存配置失败:', error);
    alert('保存失败，请重试');
  } finally {
    isSaving.value = false;
  }
};

// 激活配置
const handleActivate = async (config: LLMConfig) => {
  try {
    await activateLLMConfig(config.id);
    await loadConfigs();
  } catch (error) {
    console.error('激活配置失败:', error);
    alert('激活失败，请重试');
  }
};

// 删除配置
const handleDelete = async (config: LLMConfig) => {
  const message = config.is_active
    ? `确定要删除当前激活的配置"${config.name}"吗？删除后将自动切换到其他配置。`
    : `确定要删除配置"${config.name}"吗？`;

  if (!confirm(message)) {
    return;
  }

  try {
    await deleteLLMConfig(config.id);
    await loadConfigs();
  } catch (error) {
    console.error('删除配置失败:', error);
    alert('删除失败，请重试');
  }
};

// 测试连接（配置卡片）
const handleTestConnection = async (config: LLMConfig) => {
  if (!config.llm_provider_api_key) {
    alert('该配置未设置 API Key，无法测试连接');
    return;
  }
  if (!config.llm_provider_model) {
    alert('该配置未设置模型，无法测试连接');
    return;
  }

  isTestingConnection.value = config.id;
  try {
    const result = await testLLMConnection({
      api_format: config.api_format || 'openai_chat',
      llm_provider_url: config.llm_provider_url || undefined,
      llm_provider_api_key: config.llm_provider_api_key,
      llm_provider_model: config.llm_provider_model,
    });
    connectionTestResults.value[config.id] = result;
  } catch (error) {
    console.error('测试连接失败:', error);
    connectionTestResults.value[config.id] = {
      success: false,
      latency_ms: 0,
      message: '测试请求失败，请检查网络',
    };
  } finally {
    isTestingConnection.value = null;
  }
};

// 清除测试结果
const clearTestResult = (configId: number) => {
  delete connectionTestResults.value[configId];
};

// 测试连接（弹窗内）
const handleTestConnectionInDialog = async () => {
  if (!formData.value.llm_provider_api_key) {
    alert('请先填写 API Key');
    return;
  }
  if (!formData.value.llm_provider_model) {
    alert('请先填写模型名称');
    return;
  }

  isTestingConnectionInDialog.value = true;
  dialogTestResult.value = null;

  try {
    const result = await testLLMConnection({
      api_format: formData.value.api_format,
      llm_provider_url: formData.value.llm_provider_url || undefined,
      llm_provider_api_key: formData.value.llm_provider_api_key,
      llm_provider_model: formData.value.llm_provider_model,
    });
    dialogTestResult.value = result;
  } catch (error) {
    console.error('测试连接失败:', error);
    dialogTestResult.value = {
      success: false,
      latency_ms: 0,
      message: '测试请求失败，请检查网络',
    };
  } finally {
    isTestingConnectionInDialog.value = false;
  }
};

// 加载模型列表
const loadModels = async () => {
  if (!formData.value.llm_provider_api_key) {
    alert('请先填写 API Key');
    return;
  }

  isLoadingModels.value = true;
  try {
    const models = await getAvailableModels({
      api_format: formData.value.api_format,
      llm_provider_api_key: formData.value.llm_provider_api_key,
      llm_provider_url: formData.value.llm_provider_url || undefined,
    });
    availableModels.value = models;
    if (models.length > 0) {
      showModelDropdown.value = true;
    } else {
      alert('未获取到模型列表，请检查 API 配置是否正确');
    }
  } catch (error) {
    console.error('获取模型列表失败:', error);
    alert('获取模型列表失败，请检查网络连接和 API 配置');
  } finally {
    isLoadingModels.value = false;
  }
};

// 选择模型
const selectModel = (model: string) => {
  formData.value.llm_provider_model = model;
  showModelDropdown.value = false;
};

// 模型输入框聚焦时，只有有模型列表时才显示下拉
const onModelInputFocus = () => {
  if (availableModels.value.length > 0) {
    showModelDropdown.value = true;
  }
};

// 隐藏下拉列表
const hideDropdown = () => {
  setTimeout(() => {
    showModelDropdown.value = false;
  }, 200);
};
</script>
