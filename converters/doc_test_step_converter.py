from xml.etree import ElementTree as ET

def convert_doc_test_step(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        doc_text = config_xml.findtext("documentation") or ""

        return {
            "type": "doc-test-step",
            "name": test_step.name,
            "description": doc_text,
            "note": "Converted documentation step. Added as request description in Postman."
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert Doc Test Step '{test_step.name}': {e}")
        return None
