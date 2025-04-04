import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs, urljoin
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def get_endpoint_full_path(resource_name: str) -> str:
    """
    Get the full endpoint path for a resource
    """
    return "{{path}}/" + resource_name if resource_name else "{{path}}"

def extract_headers(config: ET.Element, namespaces: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Extract headers from the REST request configuration
    """
    headers = []
    for header in config.findall('.//con:header', namespaces) or config.findall('.//ns2:header', namespaces):
        name = header.get('name', '')
        value = header.get('value', '')
        if name and value:
            headers.append({
                "key": name,
                "value": value
            })
    return headers

def extract_assertions(config: ET.Element, namespaces: Dict[str, str]) -> List[str]:
    """
    Extract assertions from the REST request configuration
    """
    assertions = []
    for assertion in config.findall('.//con:assertion', namespaces) or config.findall('.//ns2:assertion', namespaces):
        if assertion.get('type') == 'Valid HTTP Status Codes':
            codes = assertion.get('ValidStatusCodes', '200')
            assertions.append(f"pm.test('Status code is {codes}', function() {{")
            assertions.append(f"    pm.response.to.have.status({codes});")
            assertions.append("});")
    return assertions

def convert_rest_request(test_step) -> Dict[str, Any]:
    """
    Convert a ReadyAPI REST request test step to Postman format
    """
    try:
        # Parse the test step configuration
        if isinstance(test_step.config, str):
            config = ET.fromstring(test_step.config)
        else:
            config = test_step.config

        # Get the REST request element
        namespaces = {
            'con': 'http://eviware.com/soapui/config',
            'ns2': 'http://eviware.com/soapui/config/2.0'
        }
        
        request = config.find('.//con:restRequest', namespaces)
        if request is None:
            request = config.find('.//ns2:restRequest', namespaces)
            
        if request is None:
            logger.warning(f"Could not find REST request in test step: {test_step.name}")
            return None

        # Get resource path and method name
        resource_path = request.get('resourcePath', '')
        method_name = request.get('methodName', '')
        http_method = "POST"  # default fallback

        # Try to resolve method and parameter styles from the interface section
        matched_query_params = []
        matched_headers = []
        
        # Find the interface section
        interface_section = config.find(".//con:interface", namespaces)
        if interface_section is not None:
            for resource in interface_section.findall("con:resource", namespaces):
                if resource.get("path") == resource_path:
                    for method in resource.findall("con:method", namespaces):
                        if method.get("name") == method_name:
                            http_method = method.get("method", "POST")
                            method_parameters = method.find("con:parameters", namespaces)
                            if method_parameters is not None:
                                for param in method_parameters.findall("con:parameter", namespaces):
                                    param_name = param.get("name")
                                    param_style = param.get("style", "QUERY").upper()
                                    param_value = ""
                                    for entry in request.findall('con:parameters/con:entry', namespaces):
                                        if entry.get('key') == param_name:
                                            param_value = entry.get('value', '')
                                            break
                                    if param_name and param_value:
                                        if param_style == "HEADER":
                                            matched_headers.append({"key": param_name, "value": param_value})
                                        else:
                                            matched_query_params.append({"key": param_name, "value": param_value})

        # Get endpoint and original URI
        endpoint = request.findtext('.//con:endpoint', '', namespaces) or request.findtext('.//ns2:endpoint', '', namespaces)
        original_uri = request.findtext('.//con:originalUri', '', namespaces) or request.findtext('.//ns2:originalUri', '', namespaces)
        
        # Parse the URL
        url_to_parse = original_uri or endpoint
        parsed_url = urlparse(url_to_parse) if url_to_parse else urlparse('{{baseUrl}}')
        
        # Extract URL components
        protocol = parsed_url.scheme or 'https'
        host = parsed_url.netloc.split('.') if parsed_url.netloc else []
        path = [p for p in parsed_url.path.split('/') if p]
        
        # Parse query parameters from URL
        query_params = []
        if parsed_url.query:
            query_dict = parse_qs(parsed_url.query)
            for key, values in query_dict.items():
                for value in values:
                    query_params.append({"key": key, "value": value})
        
        # Combine URL query params with interface params
        all_query_params = query_params + matched_query_params
        
        # Get headers
        headers = extract_headers(config, namespaces)
        headers.extend(matched_headers)
        
        # Determine content type
        content_type = 'application/json'  # Default
        media_type = request.get('mediaType', '').lower()
        if media_type == 'application/xml' or 'xml' in media_type:
            content_type = 'application/xml'
        
        # Add content type header if not present
        if not any(h.get("key", "").lower() == "content-type" for h in headers):
            headers.append({"key": "Content-Type", "value": content_type})
        
        # Get request body
        body = None
        body_element = request.find('.//con:request', namespaces) or request.find('.//ns2:request', namespaces)
        
        if body_element is not None and body_element.text:
            # Determine language based on content type
            language = "text"
            if 'json' in content_type.lower():
                language = "json"
            elif 'xml' in content_type.lower():
                language = "xml"
            
            body = {
                "mode": "raw",
                "raw": body_element.text.strip() or "",
                "options": {
                    "raw": {
                        "language": language
                    }
                }
            }

        # Create request object
        request_obj = {
            "name": test_step.name,
            "request": {
                "method": http_method,
                "header": headers,
                "url": {
                    "raw": url_to_parse,
                    "protocol": protocol,
                    "host": host,
                    "path": path,
                    "query": all_query_params
                }
            }
        }
        
        # Add body if present
        if body:
            request_obj["request"]["body"] = body
            
        # Add empty response array
        request_obj["response"] = []

        # Add test script if there are assertions
        assertions = extract_assertions(config, namespaces)
        if assertions:
            request_obj["event"] = [{
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": assertions
                }
            }]

        return request_obj

    except Exception as e:
        logger.error(f"Failed to convert REST request: {str(e)}")
        return None 