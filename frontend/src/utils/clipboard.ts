// AIMETA P=剪切板工具_复制文本|R=copyTextToClipboard|NR=不含UI|E=util:clipboard|X=internal|A=工具函数|D=ts|S=dom|RD=./README.ai

const fallbackCopyToClipboard = (text: string): boolean => {
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.setAttribute('readonly', '')
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    textarea.style.top = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  } catch {
    return false
  }
}

export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (!text) return false

  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    // ignore and fallback
  }

  if (typeof document === 'undefined') return false
  return fallbackCopyToClipboard(text)
}

