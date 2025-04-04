import re
from typing import List
from xml.etree import ElementTree as ET

class GroovyOperation:
    def __init__(self, op_type: str, target: str = None, value: str = None, line: str = ""):
        self.op_type = op_type  # e.g., set_header, set_property, call_function
        self.target = target
        self.value = value
        self.line = line

    def to_dict(self):
        return {
            "op_type": self.op_type,
            "target": self.target,
            "value": self.value,
            "source_line": self.line
        }

class GroovyBehaviorClassifier:
    def __init__(self, script_config):
        if isinstance(script_config, ET.Element):
            # Extract script text from XML config
            script_text = script_config.findtext('.//script') or ""
            self.script = script_text
        else:
            self.script = str(script_config)
        self.operations: List[GroovyOperation] = []

    def classify(self) -> List[GroovyOperation]:
        lines = self.script.splitlines()
        for line in lines:
            line = line.strip()
            # Match function definitions
            if match := re.match(r'def\s+(\w+)\s*\(', line):
                self.operations.append(GroovyOperation("function_def", target=match.group(1), line=line))
            # Match function calls
            elif match := re.match(r'(\w+)\s*\(.*\)', line):
                func_name = match.group(1)
                if func_name not in ["if", "for", "while", "assert", "return"]:
                    self.operations.append(GroovyOperation("function_call", target=func_name, line=line))
            # Match property set: project.setPropertyValue("key", "value")
            elif match := re.search(r'setPropertyValue\(["\'](\w+)["\'],\s*["\']?(.*?)["\']?\)', line):
                self.operations.append(GroovyOperation("set_property", target=match.group(1), value=match.group(2), line=line))
            # Match header set: headers.put("Key", "Value")
            elif match := re.search(r'headers\.put\(["\'](.+?)["\'],\s*["\']?(.*?)["\']?\)', line):
                self.operations.append(GroovyOperation("set_header", target=match.group(1), value=match.group(2), line=line))
            # Match endpoint override
            elif match := re.search(r'testRequest\.endpoint\s*=\s*["\'](.+?)["\']', line):
                self.operations.append(GroovyOperation("set_endpoint", value=match.group(1), line=line))
            # Match assertions
            elif line.startswith("assert"):
                self.operations.append(GroovyOperation("assertion", line=line))
        return self.operations

# Example usage:
if __name__ == "__main__":
    sample_script = """
    def SignInAvion(cardNumber, env) {
        def sessionID = "JSESSIONID=mock"
        headers.put("Cookie", sessionID)
        testStep.testRequest.endpoint = "https://api.domain.com"
        project.setPropertyValue("JSESSIONID", sessionID)
        return sessionID
    }
    assert response.code == 200
    SignInAvion("4519", "UAT")
    """
    classifier = GroovyBehaviorClassifier(sample_script)
    for op in classifier.classify():
        print(op.to_dict())
