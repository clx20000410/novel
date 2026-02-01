// AIMETA P=章节文本工具_清洗章节内容|R=cleanChapterText|NR=不含UI|E=util:chapterText|X=internal|A=工具函数|D=ts|S=dom|RD=./README.ai

const extractTextFromUnknownJson = (value: unknown): string | null => {
  if (!value) return null
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    for (const item of value) {
      const nested = extractTextFromUnknownJson(item)
      if (nested) return nested
    }
    return null
  }
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>
    for (const key of ['content', 'chapter_content', 'chapter_text', 'text', 'body', 'story']) {
      if (record[key]) {
        const nested = extractTextFromUnknownJson(record[key])
        if (nested) return nested
      }
    }
  }
  return null
}

export const cleanChapterText = (content: string): string => {
  if (!content) return ''

  try {
    const parsed = JSON.parse(content)
    const extracted = extractTextFromUnknownJson(parsed)
    if (extracted) {
      content = extracted
    }
  } catch {
    // not a json
  }

  let cleaned = content.replace(/^"|"$/g, '')
  cleaned = cleaned.replace(/\\n/g, '\n')
  cleaned = cleaned.replace(/\\"/g, '"')
  cleaned = cleaned.replace(/\\t/g, '\t')
  cleaned = cleaned.replace(/\\\\/g, '\\')
  return cleaned
}

