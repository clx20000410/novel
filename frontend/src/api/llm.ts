// AIMETA P=LLM_API客户端_模型配置接口|R=LLM配置CRUD|NR=不含UI逻辑|E=api:llm|X=internal|A=llmApi对象|D=fetch|S=net|RD=./README.ai
import { useAuthStore } from '@/stores/auth';

const API_PREFIX = '/api';
const LLM_BASE = `${API_PREFIX}/llm-configs`;

/**
 * API 格式类型
 */
export type ApiFormatType = 'openai_chat' | 'openai_responses' | 'anthropic' | 'google';

/**
 * API 格式选项
 */
export const API_FORMAT_OPTIONS = [
  { value: 'openai_chat' as ApiFormatType, label: 'OpenAI (Chat Completions)', description: '兼容性最好，适用于大多数服务' },
  { value: 'openai_responses' as ApiFormatType, label: 'OpenAI (Responses)', description: 'OpenAI 较新的 Responses API' },
  { value: 'anthropic' as ApiFormatType, label: 'Anthropic (Claude)', description: 'Anthropic Claude 系列模型' },
  { value: 'google' as ApiFormatType, label: 'Google (Gemini)', description: 'Google Gemini 系列模型' },
];

/**
 * LLM 配置接口（完整响应）
 */
export interface LLMConfig {
  id: number;
  user_id: number;
  name: string;
  is_active: boolean;
  api_format: ApiFormatType;
  llm_provider_url: string | null;
  llm_provider_api_key: string | null;
  llm_provider_model: string | null;
  blueprint_batch_size: number;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * 创建 LLM 配置的请求体
 */
export interface LLMConfigCreate {
  name: string;
  api_format?: ApiFormatType;
  llm_provider_url?: string;
  llm_provider_api_key?: string;
  llm_provider_model?: string;
  blueprint_batch_size?: number;
}

/**
 * 更新 LLM 配置的请求体
 */
export interface LLMConfigUpdate {
  name?: string;
  api_format?: ApiFormatType;
  llm_provider_url?: string;
  llm_provider_api_key?: string;
  llm_provider_model?: string;
  blueprint_batch_size?: number;
}

/**
 * 获取模型列表的请求体
 */
export interface ModelListRequest {
  api_format?: ApiFormatType;
  llm_provider_url?: string;
  llm_provider_api_key: string;
}

/**
 * 测试连接的请求体
 */
export interface TestConnectionRequest {
  api_format: ApiFormatType;
  llm_provider_url?: string;
  llm_provider_api_key: string;
  llm_provider_model: string;
}

/**
 * 测试连接的响应体
 */
export interface TestConnectionResponse {
  success: boolean;
  latency_ms: number;
  message: string;
}

const getHeaders = () => {
  const authStore = useAuthStore();
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authStore.token}`,
  };
};

/**
 * 获取用户的所有 LLM 配置列表
 */
export const getLLMConfigs = async (): Promise<LLMConfig[]> => {
  const response = await fetch(LLM_BASE, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error('获取 LLM 配置列表失败');
  }
  return response.json();
};

/**
 * 获取当前激活的 LLM 配置
 */
export const getActiveLLMConfig = async (): Promise<LLMConfig | null> => {
  const response = await fetch(`${LLM_BASE}/active`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error('获取激活配置失败');
  }
  return response.json();
};

/**
 * 根据 ID 获取单个 LLM 配置
 */
export const getLLMConfigById = async (id: number): Promise<LLMConfig | null> => {
  const response = await fetch(`${LLM_BASE}/${id}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error('获取 LLM 配置失败');
  }
  return response.json();
};

/**
 * 创建新的 LLM 配置
 */
export const createLLMConfig = async (config: LLMConfigCreate): Promise<LLMConfig> => {
  const response = await fetch(LLM_BASE, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error('创建 LLM 配置失败');
  }
  return response.json();
};

/**
 * 更新 LLM 配置
 */
export const updateLLMConfig = async (id: number, config: LLMConfigUpdate): Promise<LLMConfig> => {
  const response = await fetch(`${LLM_BASE}/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error('更新 LLM 配置失败');
  }
  return response.json();
};

/**
 * 删除 LLM 配置
 */
export const deleteLLMConfig = async (id: number): Promise<void> => {
  const response = await fetch(`${LLM_BASE}/${id}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error('删除 LLM 配置失败');
  }
};

/**
 * 激活指定的 LLM 配置
 */
export const activateLLMConfig = async (id: number): Promise<LLMConfig> => {
  const response = await fetch(`${LLM_BASE}/${id}/activate`, {
    method: 'PUT',
    headers: getHeaders(),
  });
  if (!response.ok) {
    throw new Error('激活 LLM 配置失败');
  }
  return response.json();
};

/**
 * 获取可用的模型列表
 */
export const getAvailableModels = async (request: ModelListRequest): Promise<string[]> => {
  const response = await fetch(`${LLM_BASE}/models`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    // 获取模型列表失败时返回空数组，不影响主流程
    return [];
  }
  return response.json();
};

/**
 * 测试 LLM 连接
 */
export const testLLMConnection = async (request: TestConnectionRequest): Promise<TestConnectionResponse> => {
  const response = await fetch(`${LLM_BASE}/test`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error('测试连接失败');
  }
  return response.json();
};

// ==================== 兼容旧接口 ====================

/**
 * @deprecated 请使用 getActiveLLMConfig 代替
 * 获取用户的 LLM 配置（兼容旧接口）
 */
export const getLLMConfig = async (): Promise<LLMConfig | null> => {
  return getActiveLLMConfig();
};

/**
 * @deprecated 请使用 createLLMConfig 或 updateLLMConfig 代替
 * 创建或更新 LLM 配置（兼容旧接口）
 */
export const createOrUpdateLLMConfig = async (config: Partial<LLMConfigCreate>): Promise<LLMConfig> => {
  // 尝试获取激活配置
  const activeConfig = await getActiveLLMConfig();
  if (activeConfig) {
    // 更新激活配置
    return updateLLMConfig(activeConfig.id, config);
  } else {
    // 创建新配置
    return createLLMConfig({
      name: '默认配置',
      ...config,
    } as LLMConfigCreate);
  }
};
