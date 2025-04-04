from xml.etree import ElementTree as ET

def convert_rest_request(test_step, context):
    try:
        if isinstance(test_step.config, str):
            config_xml = ET.fromstring(test_step.config)
        else:
            config_xml = test_step.config

        namespaces = {'con': 'http://eviware.com/soapui/config'}
        request_element = config_xml.find(".//con:restRequest", namespaces) or config_xml.find(".//con:request", namespaces)
        
        if request_element is None:
            print(f"[WARN] No request element found in step '{test_step.name}'")
            return None
            
        method = request_element.attrib.get("method", "GET")
        endpoint = request_element.findtext("con:endpoint", "", namespaces) or ""
        request_name = test_step.name

        headers = []
        for h in request_element.findall(".//con:headers/con:entry", namespaces):
            headers.append({"key": h.attrib.get('key', ''), "value": h.text or ""})

        body = request_element.findtext("con:request", "", namespaces) or ""

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
            }
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert REST step '{test_step.name}': {e}")
        return None
