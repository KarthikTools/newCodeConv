from xml.etree import ElementTree as ET

def convert_property_transfer_step(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        transfers = config_xml.findall("transfer")

        mappings = []
        for transfer in transfers:
            source_step = transfer.findtext("sourceStep")
            source_prop = transfer.findtext("sourceProperty")
            target_step = transfer.findtext("targetStep")
            target_prop = transfer.findtext("targetProperty")
            xpath = transfer.findtext("sourcePath") or ""

            mappings.append({
                "from_step": source_step,
                "from_property": source_prop,
                "from_xpath": xpath,
                "to_step": target_step,
                "to_property": target_prop
            })

        return {
            "type": "property-transfer",
            "transfers": mappings,
            "note": f"Mapped properties from '{test_step.name}'"
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert Property Transfer step '{test_step.name}': {e}")
        return None
