import re

file_path = 'frontend/src/lib/experimentTypes.ts'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the instrumentFields for surface_tension
old_fields = """    instrumentFields: [
      { fieldKey: 'surface_tension_val', label: '表面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'interface_tension_val', label: '界面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' }
    ],"""

new_fields = """    instrumentFields: [
      { fieldKey: 'water_surface_tension', label: '纯水表面张力测试', unit: 'mN/m', maxReadings: 2, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'fluid_surface_tension', label: '表面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' },
      { fieldKey: 'fluid_interface_tension', label: '界面张力测试值', unit: 'mN/m', maxReadings: 5, targetInstrumentId: 5, readingKey: '张力' }
    ],"""

if old_fields in content:
    content = content.replace(old_fields, new_fields)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully updated surface_tension fields in experimentTypes.ts")
else:
    print("Failed to find old fields in experimentTypes.ts")
