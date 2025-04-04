from xml.etree import ElementTree as ET

def convert_conditional_goto_step(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        target_step = config_xml.findtext("targetStep")
        condition = config_xml.findtext("condition") or "true"

        script = f"""
        if ({condition}) {{
            postman.setNextRequest("{target_step}");
        }}
        """

        return {
            "type": "conditional-goto",
            "name": test_step.name,
            "event": "test",
            "script": script,
            "note": f"Conditional jump to step '{target_step}' based on expression: {condition}"
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert Conditional Goto step '{test_step.name}': {e}")
        return None
