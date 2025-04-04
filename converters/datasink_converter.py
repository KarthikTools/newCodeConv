from xml.etree import ElementTree as ET

def convert_datasink_step(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        target = config_xml.findtext("dataSinkTarget") or "file"
        filename = config_xml.findtext("filename") or "output.csv"

        return {
            "type": "datasink",
            "name": test_step.name,
            "destination": target,
            "filename": filename,
            "note": "Simulated DataSink: log or save variable values in Postman test script manually."
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert DataSink step '{test_step.name}': {e}")
        return None
