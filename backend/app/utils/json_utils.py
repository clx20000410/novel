# AIMETA P=JSON工具_JSON解析和修复|R=安全解析_格式修复|NR=不含业务逻辑|E=parse_json_safely|X=internal|A=工具函数|D=json|S=none|RD=./README.ai
import json
import re


def remove_think_tags(raw_text: str) -> str:
    """移除 <think></think> 标签，避免污染结果。"""
    if not raw_text:
        return raw_text
    return re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()


def unwrap_markdown_json(raw_text: str) -> str:
    """从 Markdown 或普通文本中提取 JSON 字符串。"""
    if not raw_text:
        return raw_text

    trimmed = raw_text.strip()

    fence_match = re.search(r"```(?:json|JSON)?\s*(.*?)\s*```", trimmed, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        if candidate:
            return candidate

    json_start_candidates = [idx for idx in (trimmed.find("{"), trimmed.find("[")) if idx != -1]
    if json_start_candidates:
        start_idx = min(json_start_candidates)
        closing_brace = trimmed.rfind("}")
        closing_bracket = trimmed.rfind("]")
        end_idx = max(closing_brace, closing_bracket)
        if end_idx != -1 and end_idx > start_idx:
            candidate = trimmed[start_idx : end_idx + 1].strip()
            if candidate:
                return candidate

    return trimmed


def sanitize_json_like_text(raw_text: str) -> str:
    """对可能含有未转义换行/引号的 JSON 文本进行清洗。"""
    if not raw_text:
        return raw_text

    result = []
    in_string = False
    escape_next = False
    length = len(raw_text)
    i = 0
    while i < length:
        ch = raw_text[i]
        if in_string:
            if escape_next:
                result.append(ch)
                escape_next = False
            elif ch == "\\":
                result.append(ch)
                escape_next = True
            elif ch == '"':
                j = i + 1
                while j < length and raw_text[j] in " \t\r\n":
                    j += 1

                if j >= length or raw_text[j] in "}]":
                    in_string = False
                    result.append(ch)
                elif raw_text[j] in ",:":
                    in_string = False
                    result.append(ch)
                else:
                    result.extend(["\\", '"'])
            elif ch == "\n":
                result.extend(["\\", "n"])
            elif ch == "\r":
                result.extend(["\\", "r"])
            elif ch == "\t":
                result.extend(["\\", "t"])
            else:
                result.append(ch)
        else:
            if ch == '"':
                in_string = True
            result.append(ch)
        i += 1

    return "".join(result)


def fix_json_missing_commas(raw_text: str) -> str:
    """修复 JSON 中缺少的逗号（常见于 AI 生成的 JSON）。

    处理以下情况：
    1. "value" "key" -> "value", "key"
    2. "value"\\n"key" -> "value",\\n"key"
    3. }\\n{ -> },\\n{
    4. ]\\n[ -> ],\\n[
    5. 数字/布尔值后缺少逗号
    """
    if not raw_text:
        return raw_text

    # 修复 "..." 后面直接跟 "..." 的情况（缺少逗号）
    # 匹配: "value" 后面跟着空白和 "key"
    text = re.sub(r'"\s*\n\s*"', '",\n"', raw_text)

    # 修复 } 后面直接跟 { 的情况
    text = re.sub(r'}\s*\n\s*{', '},\n{', text)

    # 修复 ] 后面直接跟 [ 的情况
    text = re.sub(r']\s*\n\s*\[', '],\n[', text)

    # 修复 } 后面直接跟 " 的情况（对象后面跟字符串键）
    text = re.sub(r'}\s*\n\s*"', '},\n"', text)

    # 修复 ] 后面直接跟 " 的情况
    text = re.sub(r']\s*\n\s*"', '],\n"', text)

    # 修复数字后面直接跟 " 的情况
    text = re.sub(r'(\d)\s*\n\s*"', r'\1,\n"', text)

    # 修复 true/false/null 后面直接跟 " 的情况
    text = re.sub(r'(true|false|null)\s*\n\s*"', r'\1,\n"', text)

    return text


def is_json_complete(raw_text: str) -> bool:
    """检查 JSON 字符串是否完整（括号匹配）。

    Returns:
        True 如果 JSON 看起来完整，False 如果被截断
    """
    if not raw_text:
        return False

    # 提取 JSON 部分
    text = unwrap_markdown_json(raw_text).strip()
    if not text:
        return False

    # 计算括号平衡
    stack = []
    in_string = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue

        if ch == '\\' and in_string:
            escape_next = True
            continue

        if ch == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch in '{[':
            stack.append(ch)
        elif ch == '}':
            if not stack or stack[-1] != '{':
                return False
            stack.pop()
        elif ch == ']':
            if not stack or stack[-1] != '[':
                return False
            stack.pop()

    # 如果 stack 为空且不在字符串中，则 JSON 完整
    return len(stack) == 0 and not in_string


def parse_json_safely(raw_text: str) -> dict | list | None:
    """安全地解析 JSON，自动尝试多种修复策略。

    按顺序尝试：
    1. 直接解析
    2. 提取 markdown 代码块后解析
    3. 清洗特殊字符后解析
    4. 修复缺少的逗号后解析
    5. 组合所有修复策略

    Returns:
        解析成功返回 dict 或 list，失败返回 None
    """
    if not raw_text:
        return None

    # 尝试 1: 直接解析
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # 尝试 2: 提取 markdown 代码块
    unwrapped = unwrap_markdown_json(raw_text)
    try:
        return json.loads(unwrapped)
    except json.JSONDecodeError:
        pass

    # 尝试 3: 清洗特殊字符
    sanitized = sanitize_json_like_text(unwrapped)
    try:
        return json.loads(sanitized)
    except json.JSONDecodeError:
        pass

    # 尝试 4: 修复缺少的逗号
    fixed = fix_json_missing_commas(sanitized)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 尝试 5: 先修复逗号，再清洗
    fixed_then_sanitized = sanitize_json_like_text(fix_json_missing_commas(unwrapped))
    try:
        return json.loads(fixed_then_sanitized)
    except json.JSONDecodeError:
        pass

    return None
