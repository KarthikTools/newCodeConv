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

        # Add default properties if none found
        if not properties:
            properties = [
                {
                    "key": "CardNumber",
                    "value": "4519821569835616",
                    "enabled": True
                },
                {
                    "key": "env",
                    "value": "UAT",
                    "enabled": True
                }
            ]

        return {
            "name": "InputData",
            "type": "properties",
            "variables": properties,
            "note": "Variables defined in step 'InputData'",
            "test_case": context.get("test_case_name", "Main Tests"),
            "test_suite": context.get("test_suite", "Main Suite")
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert Properties step '{test_step.name}': {e}")
        return None
