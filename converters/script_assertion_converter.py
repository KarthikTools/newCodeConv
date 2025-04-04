from xml.etree import ElementTree as ET
from .script_assertion_converter import extract_assertions_from_node

def convert_rest_request(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        request_element = config_xml.find(".//restRequest") or config_xml
        method = request_element.attrib.get("method", "GET")
        endpoint = request_element.findtext("endpoint") or ""
        request_name = test_step.name

        headers = []
        for h in request_element.findall(".//headers/entry"):
            headers.append({"key": h.attrib['key'], "value": h.text or ""})

        body = request_element.findtext("request") or ""

        # Extract embedded assertions (if any)
        assertions = extract_assertions_from_node(request_element)
        test_script = "\n".join(assertions) if assertions else ""

        return {
            "name": request_name,
            "request": {
                "method": method,
                "header": headers,
                "url": endpoint,
                "body": {
                    "mode": "raw",
                    "raw": body
                },
                "description": "Converted from ReadyAPI"
            },
            "event": {
                "test": test_script
            }
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert REST step '{test_step.name}': {e}")
        return None
