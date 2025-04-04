from xml.etree import ElementTree as ET

def convert_properties_step(test_step, context):
    """Convert a ReadyAPI Properties test step to Postman format"""
    try:
        if isinstance(test_step.config, str):
            config_xml = ET.fromstring(test_step.config)
        else:
            config_xml = test_step.config

        namespaces = {'con': 'http://eviware.com/soapui/config'}
        properties = []
        
        # Extract properties from the config
        for prop in config_xml.findall('.//con:property', namespaces):
            name = prop.findtext('.//con:name', '', namespaces)
            value = prop.findtext('.//con:value', '', namespaces)
            if name:
                properties.append({
                    "key": name,
                    "value": value or "",
                    "enabled": True
                })

        return {
            "name": test_step.name,
            "type": "properties",
            "variables": properties,
            "note": f"Variables defined in step '{test_step.name}'",
            "test_case": context.get("test_case_name", "Main Tests")
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert Properties step '{test_step.name}': {e}")
        return None
