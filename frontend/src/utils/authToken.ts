// AIMETA P=认证令牌存储_统一存取|R=令牌存取_URL令牌处理|NR=不含UI|E=authToken|X=internal|A=tokenStorage|D=ts|S=storage|RD=./README.ai
const TOKEN_KEY = 'token'

const resolveTokenStorage = () => {
  const preference = import.meta.env.VITE_TOKEN_STORAGE
  if (preference === 'session') {
    return sessionStorage
  }
  if (preference === 'local') {
    return localStorage
  }
  return import.meta.env.MODE === 'production' ? sessionStorage : localStorage
}

const tokenStorage = resolveTokenStorage()

export const getStoredToken = () => {
  const token = tokenStorage.getItem(TOKEN_KEY)
  if (token) {
    return token
  }
  if (tokenStorage !== localStorage) {
    const legacy = localStorage.getItem(TOKEN_KEY)
    if (legacy) {
      tokenStorage.setItem(TOKEN_KEY, legacy)
      localStorage.removeItem(TOKEN_KEY)
      return legacy
    }
  }
  return null
}

export const setStoredToken = (token: string) => {
  tokenStorage.setItem(TOKEN_KEY, token)
  if (tokenStorage !== localStorage) {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export const clearStoredToken = () => {
  tokenStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(TOKEN_KEY)
}

export const allowUrlToken = () =>
  import.meta.env.VITE_ALLOW_URL_TOKEN === 'true' || import.meta.env.MODE !== 'production'

const parseTokenFromSearch = () => {
  const url = new URL(window.location.href)
  const token = url.searchParams.get('token')
  if (!token) {
    return null
  }
  url.searchParams.delete('token')
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`)
  return token
}

const parseTokenFromHash = () => {
  const rawHash = window.location.hash.replace(/^#/, '')
  if (!rawHash) {
    return null
  }
  const params = new URLSearchParams(rawHash)
  const token = params.get('token')
  if (!token) {
    return null
  }
  params.delete('token')
  const newHash = params.toString()
  const url = new URL(window.location.href)
  url.hash = newHash ? `#${newHash}` : ''
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`)
  return token
}

export const consumeTokenFromLocation = () => {
  const tokenFromHash = parseTokenFromHash()
  if (tokenFromHash) {
    return tokenFromHash
  }
  return parseTokenFromSearch()
}
