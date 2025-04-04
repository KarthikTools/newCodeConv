import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

class ReadyAPIInterface:
    def __init__(self, name, path, method, endpoint, media_type, headers=None, body=None, description=None):
        self.name = name
        self.path = path
        self.method = method
        self.endpoint = endpoint
        self.media_type = media_type
        self.headers = headers or {}
        self.body = body or ""
        self.description = description or ""

class ReadyAPITestStep:
    def __init__(self, step_type, name, config):
        self.step_type = step_type
        self.name = name
        self.config = config

class ReadyAPITestCase:
    def __init__(self, name):
        self.name = name
        self.test_steps: List[ReadyAPITestStep] = []
        self.properties: Dict[str, str] = {}

class ReadyAPITestSuite:
    def __init__(self, name):
        self.name = name
        self.test_cases: List[ReadyAPITestCase] = []
        self.resources: List[ReadyAPIInterface] = []

class ReadyAPIProject:
    def __init__(self, name):
        self.name = name
        self.interfaces: List[ReadyAPIInterface] = []
        self.test_suites: List[ReadyAPITestSuite] = []
        self.properties: Dict[str, str] = {}


def parse_project_file(xml_path: str) -> ReadyAPIProject:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Handle namespaces properly
    namespaces = {'con': 'http://eviware.com/soapui/config'}
    project_name = root.attrib.get('name', 'UnknownProject')
    project = ReadyAPIProject(project_name)

    # Parse properties
    for prop in root.findall('.//con:properties/con:property', namespaces):
        name = prop.find('con:name', namespaces)
        value = prop.find('con:value', namespaces)
        if name is not None and value is not None:
            project.properties[name.text] = value.text or ''

    # Parse interfaces and their resources
    for iface in root.findall('.//con:interface', namespaces):
        if iface.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}type') == 'con:RestService':
            for resource in iface.findall('.//con:resource', namespaces):
                resource_name = resource.attrib.get('name', '')
                resource_path = resource.attrib.get('path', '')
                
                for method in resource.findall('.//con:method', namespaces):
                    method_type = method.attrib.get('method', 'GET')
                    
                    for request in method.findall('.//con:request', namespaces):
                        endpoint = request.find('.//con:endpoint', namespaces)
                        endpoint_url = endpoint.text if endpoint is not None else ''
                        media_type = request.attrib.get('mediaType', 'application/json')
                        
                        # Extract headers
                        headers = {}
                        for header in request.findall('.//con:entry', namespaces):
                            key = header.find('con:key', namespaces)
                            value = header.find('con:value', namespaces)
                            if key is not None and value is not None:
                                headers[key.text] = value.text
                        
                        # Extract request body
                        body = request.find('.//con:request', namespaces)
                        body_text = body.text if body is not None else ""
                        
                        # Extract description
                        description = request.find('.//con:description', namespaces)
                        description_text = description.text if description is not None else ""
                        
                        interface = ReadyAPIInterface(
                            name=resource_name,
                            path=resource_path,
                            method=method_type,
                            endpoint=endpoint_url,
                            media_type=media_type,
                            headers=headers,
                            body=body_text,
                            description=description_text
                        )
                        project.interfaces.append(interface)

    # Parse test suites
    for suite in root.findall('.//con:testSuite', namespaces):
        test_suite = ReadyAPITestSuite(suite.attrib.get('name', ''))
        
        # Extract resources for the test suite
        for resource in suite.findall('.//con:resource', namespaces):
            resource_name = resource.attrib.get('name', '')
            resource_path = resource.attrib.get('path', '')
            
            for method in resource.findall('.//con:method', namespaces):
                method_type = method.attrib.get('method', 'GET')
                
                for request in method.findall('.//con:request', namespaces):
                    endpoint = request.find('.//con:endpoint', namespaces)
                    endpoint_url = endpoint.text if endpoint is not None else ''
                    media_type = request.attrib.get('mediaType', 'application/json')
                    
                    # Extract headers
                    headers = {}
                    for header in request.findall('.//con:entry', namespaces):
                        key = header.find('con:key', namespaces)
                        value = header.find('con:value', namespaces)
                        if key is not None and value is not None:
                            headers[key.text] = value.text
                    
                    # Extract request body
                    body = request.find('.//con:request', namespaces)
                    body_text = body.text if body is not None else ""
                    
                    # Extract description
                    description = request.find('.//con:description', namespaces)
                    description_text = description.text if description is not None else ""
                    
                    interface = ReadyAPIInterface(
                        name=resource_name,
                        path=resource_path,
                        method=method_type,
                        endpoint=endpoint_url,
                        media_type=media_type,
                        headers=headers,
                        body=body_text,
                        description=description_text
                    )
                    test_suite.resources.append(interface)
        
        for case in suite.findall('.//con:testCase', namespaces):
            test_case = ReadyAPITestCase(case.attrib.get('name', ''))
            
            # Parse test case properties
            for prop in case.findall('.//con:properties/con:property', namespaces):
                name = prop.find('con:name', namespaces)
                value = prop.find('con:value', namespaces)
                if name is not None and value is not None:
                    test_case.properties[name.text] = value.text or ''
            
            for step in case.findall('.//con:testStep', namespaces):
                step_type = step.attrib.get('type', '')
                step_name = step.attrib.get('name', '')
                config = step.find('.//con:config', namespaces)
                
                if config is not None:
                    # Keep config as XML element instead of string
                    test_case.test_steps.append(
                        ReadyAPITestStep(step_type, step_name, config)
                    )
            
            if test_case.test_steps:  # Only add test cases that have steps
                test_suite.test_cases.append(test_case)
        
        if test_suite.test_cases:  # Only add test suites that have cases
            project.test_suites.append(test_suite)

    return project
