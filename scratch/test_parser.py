import json
import re

text = """<think></think>
{"ph_value": 6.73, "temperature": 25.0, "pts": 1000.0}"""

def _parse_json_response(text):
    text = text.strip()
    text = re.sub(r',\s*\.\.\.\s*', '', text)
    text = re.sub(r'\.\.\.', '', text)
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_block_match:
        json_text = code_block_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    start = text.find('{')
    if start == -1:
        match = re.search(r'\{', text)
        if match:
            start = match.start()
        else:
            return {'error': '响应中未找到JSON对象', 'raw_text': text}

    depth = 0
    for i in range(len(text) - 1, start - 1, -1):
        if text[i] == '}':
            json_str = text[start:i + 1]
            depth_check = 0
            valid = True
            for c in json_str:
                if c == '{':
                    depth_check += 1
                elif c == '}':
                    depth_check -= 1
                    if depth_check < 0:
                        valid = False
                        break
            if valid and depth_check == 0:
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                json_str = text[start:i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    return {'error': f'JSON解析错误: {e}', 'raw_text': text}
    return {'error': 'JSON对象未正确闭合', 'raw_text': text}

print(_parse_json_response(text))
