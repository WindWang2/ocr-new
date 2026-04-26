import os

file_path = 'frontend/src/lib/experimentTypes.ts'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last closing brace of the EXPERIMENT_SCHEMAS object
last_brace_idx = content.rfind('}')

test_schema = """
  test: {
    type: 'test',
    label: '全场景仪表测试',
    description: '系统全量化验证：按批次查看并触发 D0~D8 所有仪表',
    icon: '🔬',
    manualParams: [],
    instrumentFields: []
  }
"""

if last_brace_idx != -1:
    new_content = content[:last_brace_idx].rstrip()
    if not new_content.endswith(','):
        new_content += ','
    new_content += test_schema + "\n}\n"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Added 'test' schema to experimentTypes.ts")
else:
    print("Could not find the end of EXPERIMENT_SCHEMAS")
