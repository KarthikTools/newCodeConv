from xml.etree import ElementTree as ET

def convert_delay_step(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        delay_ms = config_xml.findtext("delay", default="0")
        ms = int(delay_ms)

        script = f"setTimeout(() => {{ console.log('Delayed step executed'); }}, {ms});"

        return {
            "type": "delay",
            "name": test_step.name,
            "event": "pre-request",
            "script": script,
            "note": f"Simulated delay of {ms} ms using setTimeout."
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert Delay step '{test_step.name}': {e}")
        return None
