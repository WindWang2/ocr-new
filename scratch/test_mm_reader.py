from instrument_reader import MultimodalModelReader
import json

reader = MultimodalModelReader()
text = """<think></think>
{"ph_value": 6.73, "temperature": 25.0, "pts": 1000.0}"""

parsed = reader._parse_json_response(text)
print('Parsed:', parsed)

# Also test the logic in analyze_image
instrument_type = "F3"
from instrument_reader import DynamicInstrumentLibrary
template = DynamicInstrumentLibrary.get_template(instrument_type)
if template:
    for field in template.get('fields', []):
        f_name = field['name']
        if f_name not in parsed:
            parsed[f_name] = None
        else:
            try:
                if parsed[f_name] is not None:
                    parsed[f_name] = float(str(parsed[f_name]).replace(',', ''))
            except Exception as e:
                print('Error casting:', e)

print('After Float Cast:', parsed)
