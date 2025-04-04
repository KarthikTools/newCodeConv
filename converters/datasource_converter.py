from xml.etree import ElementTree as ET

def convert_datasource_step(test_step, context):
    try:
        config_xml = ET.fromstring(test_step.config)
        datasource_type = config_xml.attrib.get("class", "")
        ds_properties = config_xml.find("properties")

        if datasource_type.lower().endswith("datasourcedirectorystep"):
            file_path = ds_properties.findtext("entry[@key='file']")
            delimiter = ds_properties.findtext("entry[@key='delimiter']", ",")
        else:
            file_path = ds_properties.findtext("entry[@key='xlsFile']")
            delimiter = ","

        return {
            "type": "data-source",
            "source_type": "csv" if file_path.endswith(".csv") else "excel",
            "file_path": file_path,
            "delimiter": delimiter,
            "note": f"Datasource step '{test_step.name}' mapped for iteration"
        }
    except Exception as e:
        print(f"[ERROR] Failed to convert DataSource step '{test_step.name}': {e}")
        return None
