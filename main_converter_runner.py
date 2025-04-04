import logging
import json
import argparse
import os
import uuid
import re
from typing import Dict, List, Any, Optional
from readyapi_project_parser import parse_project_file
from execution_flow_builder import ExecutionFlowBuilder
from step_conversion_logger import StepConversionLogger
from test_step_dispatcher import dispatch_step_conversion
from postman_collection_builder import build_postman_collection
from converters.rest_request_converter import convert_rest_request
from rest_request_converter import get_endpoint_full_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure that the postman_environment_builder.py file is created and contains the required function `build_postman_environment`
try:
    from postman_environment_builder import build_postman_environment
except ImportError:
    def build_postman_environment(env_name, properties, output_file):
        print("[WARNING] postman_environment_builder module not found. Skipping environment export.")


def extract_api_endpoints(project) -> List[Dict[str, Any]]:
    """
    Extract API endpoints from the ReadyAPI project
    """
    endpoints = []
    endpoint_urls = set()  # To track unique endpoints
    
    # Interface names map for prefixing endpoints to match manual format
    interface_names = {}
    
    # Extract from interfaces
    if hasattr(project, 'interfaces') and project.interfaces:
        for interface in project.interfaces:
            if hasattr(interface, 'name') and interface.name:
                # Store interface names for later prefixing
                if hasattr(interface, 'resources') and interface.resources:
                    for resource in interface.resources:
                        if hasattr(resource, 'name') and resource.name:
                            interface_names[resource.name] = interface.name
    
    # Extract from interfaces again to create endpoints
    if hasattr(project, 'interfaces') and project.interfaces:
        for interface in project.interfaces:
            if hasattr(interface, 'resources') and interface.resources:
                for resource in interface.resources:
                    if hasattr(resource, 'name') and resource.name:
                        # Get the endpoint path from the converter
                        endpoint_path = get_endpoint_full_path(resource.name)
                        
                        # Get the base URL
                        base_url = ""
                        if hasattr(interface, 'endpoints') and interface.endpoints:
                            base_url = interface.endpoints[0]
                        
                        # Combine to form full URL
                        full_url = base_url
                        if endpoint_path:
                            if base_url.endswith('/') and endpoint_path.startswith('/'):
                                full_url = base_url + endpoint_path[1:]
                            else:
                                full_url = base_url + endpoint_path
                        
                        if full_url and full_url not in endpoint_urls:
                            endpoint_urls.add(full_url)
                            
                            # Parse endpoint
                            from urllib.parse import urlparse
                            parsed = urlparse(full_url)
                            protocol = parsed.scheme or 'https'
                            host = parsed.netloc.split('.')
                            path_parts = [p for p in parsed.path.split('/') if p]
                            
                            # Determine content type
                            content_type = 'application/json'
                            if hasattr(resource, 'method') and resource.method:
                                method = resource.method
                            else:
                                method = "GET"
                            
                            # Create endpoint object to match manual format
                            interface_prefix = interface_names.get(resource.name, "")
                            endpoint_name = f"{interface_prefix} - {resource.name}" if interface_prefix else resource.name
                            
                            endpoint = {
                                "name": endpoint_name,
                                "request": {
                                    "method": method,
                                    "header": [],
                                    "url": {
                                        "raw": full_url,
                                        "protocol": protocol,
                                        "host": host,
                                        "path": path_parts
                                    },
                                    "description": "Converted from ReadyAPI REST request" 
                                }
                            }
                            
                            # Add body if applicable based on method
                            if method in ["POST", "PUT", "PATCH"]:
                                # Determine language based on content type
                                language = "json"
                                if 'xml' in content_type.lower():
                                    language = "xml"
                                
                                endpoint["request"]["body"] = {
                                    "mode": "raw",
                                    "raw": "",
                                    "options": {
                                        "raw": {
                                            "language": language
                                        }
                                    }
                                }
                            
                            endpoints.append(endpoint)
    
    return endpoints


def sanitize_url(url):
    """
    Parse a URL and create a structure that preserves the original URL
    while also making it available through variables
    """
    if not url:
        return {
            "raw": "{{baseUrl}}",
            "host": ["{{baseUrl}}"],
            "path": []
        }
    
    # Parse the URL to extract components
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    # Extract components
    protocol = parsed.scheme or "https"
    host_parts = parsed.netloc.split('.') if parsed.netloc else []
    path_parts = [p for p in parsed.path.split('/') if p] if parsed.path else []
    
    # Create the URL object with both the original URL and variable options
    url_obj = {
        "raw": url,  # Keep the original complete URL
        "protocol": protocol,
        "host": host_parts,
        "path": path_parts,
        "description": f"Original URL: {url} - Can also use {{baseUrl}}{{path}} with environment variables"
    }
    
    return url_obj


def sanitize_name(name: str) -> str:
    """Sanitize a name to remove any project-specific references"""
    if not name:
        return ""
        
    # Define specific terms to remove - be very aggressive
    specific_terms = [
        "mobiliser", "avion", "rewards", "rbc", "royal", "bank", "sterbcroyalbank",
        "rbcbanking", "banking", "scotia", "cibc", "td", "bmo", "scotiabank",
        "cashback", "saving", "2000k", "5000k", "test", "regression", "api",
        "tc_01", "tc_02", "tc_03", "tc_04", "tc_05", "tc01", "tc02", "tc03",
        "tc_", "_tc", "tc", "testcase", "_test_", "and"
    ]
    
    # Make a copy of the name
    sanitized = name
    
    # Remove specific terms
    for term in specific_terms:
        # Try different case variations - use word boundaries for more precise matching
        sanitized = re.sub(r'\b' + re.escape(term) + r'\b', '', sanitized, flags=re.IGNORECASE)
    
    # Also remove any numeric sequences
    sanitized = re.sub(r'\d+k', '', sanitized)  # Remove patterns like 2000k, 5000k
    sanitized = re.sub(r'_\d+', '', sanitized)  # Remove patterns like _01, _02
    sanitized = re.sub(r'\d+', '', sanitized)   # Remove any remaining numbers
    
    # Clean up the result
    sanitized = sanitized.strip()
    sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with a single one
    sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
    
    # Add generic prefixes based on original naming patterns
    if not sanitized:
        if "test" in name.lower():
            return "TestCase"
        elif "tc_" in name.lower() or name.lower().startswith("tc"):
            return "TestCase"
        elif "suite" in name.lower():
            return "TestSuite"
        elif "cash" in name.lower() or "saving" in name.lower():
            return "FinancialService"
        else:
            return "APITest"
    
    # Add generic prefixes for commonly used patterns
    if sanitized.lower() == "cashbackandsaving":
        return "FinancialService"
    elif len(sanitized) <= 2:  # If we're left with something too short
        return "APITest"
    
    return sanitized


def sanitize_properties(properties: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert properties to generic versions to avoid exposing sensitive data"""
    sanitized = []
    generic_values = {
        "cardnumber": "{{cardNumber}}",
        "card": "{{cardNumber}}",
        "username": "{{username}}",
        "password": "{{password}}",
        "token": "{{token}}",
        "session": "{{sessionId}}",
        "url": "{{baseUrl}}",
        "endpoint": "{{endpoint}}",
        "auth": "{{authToken}}",
        "id": "{{id}}",
        "key": "{{apiKey}}"
    }
    
    for key, value in properties.items():
        # Create sanitized version
        sanitized_value = value
        
        # Check if this property might contain sensitive data
        key_lower = key.lower()
        for pattern, replacement in generic_values.items():
            if pattern in key_lower:
                sanitized_value = replacement
                break
        
        # Add property with sanitized value
        sanitized.append({
            "key": key,
            "value": sanitized_value,
            "enabled": True
        })
    
    return sanitized


def run_readyapi_to_postman(input_file: str, output_file: str, env_file: str = None) -> None:
    """
    Run the ReadyAPI to Postman conversion process
    
    Args:
        input_file: Path to the ReadyAPI project XML file
        output_file: Path to the output Postman collection JSON file
        env_file: Path to the output Postman environment JSON file
    """
    try:
        # Parse the ReadyAPI project
        project = parse_project_file(input_file)
        if not project:
            logger.error("Failed to parse ReadyAPI project")
            return

        # Use the original project name - it's important to maintain the actual project structure
        project_name = project.name if hasattr(project, 'name') and project.name else "ReadyAPI_Project"

        # Convert test steps
        converted_steps = []
        
        # Extract API endpoints from the project
        api_endpoints = extract_api_endpoints(project)
        logger.info(f"Extracted {len(api_endpoints)} API endpoints from the project")
        
        for test_suite in project.test_suites:
            # Keep the original test suite name - these are important identifiers in the test structure
            logger.info(f"Processing test suite: {test_suite.name}")
            
            for test_case in test_suite.test_cases:
                # Keep the original test case name - these are important identifiers in the test structure
                logger.info(f"Processing test case: {test_case.name}")
                
                # Add test case properties as an input data step
                if hasattr(test_case, 'properties') and test_case.properties:
                    # Sanitize the properties to avoid exposing sensitive data
                    property_variables = sanitize_properties(test_case.properties)
                    
                    if property_variables:
                        properties_step = {
                            "type": "properties",
                            "name": "InputData",
                            "test_suite": test_suite.name,
                            "test_case": test_case.name,
                            "variables": property_variables,
                            "note": f"Variables defined for test case: {test_case.name}"
                        }
                        converted_steps.append(properties_step)
                
                for test_step in test_case.test_steps:
                    # Skip steps that are clearly not supported
                    if hasattr(test_step, 'name'):
                        if test_step.name.lower() in ["cardnumber", "env"]:
                            logger.warning(f"Skipping unsupported step type: {test_step.name}")
                            continue
                    
                    # Determine step type based on available attributes
                    step_type = getattr(test_step, 'step_type', '').lower()
                    config = getattr(test_step, 'config', None)
                    
                    # Convert REST requests
                    is_rest_request = (
                        (step_type and 'rest' in step_type) or
                        (isinstance(config, str) and 'restRequest' in config)
                    )
                    
                    if is_rest_request:
                        logger.info(f"Converting REST request step: {test_step.name}")
                        converted_step = convert_rest_request(test_step)
                        if converted_step:
                            # Sanitize URLs while preserving the original URL
                            if "request" in converted_step:
                                if "url" in converted_step["request"]:
                                    url = converted_step["request"]["url"]
                                    if isinstance(url, dict) and "raw" in url:
                                        # Preserve the original URL but structure it with components
                                        raw_url = url.get("raw")
                                        url_obj = sanitize_url(raw_url)
                                        converted_step["request"]["url"] = url_obj
                                    elif isinstance(url, str):
                                        # Convert string URLs to structured format
                                        converted_step["request"]["url"] = sanitize_url(url)
                            
                            converted_step["test_suite"] = test_suite.name
                            converted_step["test_case"] = test_case.name
                            converted_steps.append(converted_step)
                    
                    # Convert properties steps
                    elif hasattr(test_step, 'properties') and test_step.properties:
                        logger.info(f"Converting properties step: {test_step.name}")
                        # Sanitize the properties to avoid exposing sensitive data
                        variables = sanitize_properties(test_step.properties)
                        
                        converted_step = {
                            "type": "properties",
                            "name": test_step.name,
                            "test_suite": test_suite.name,
                            "test_case": test_case.name,
                            "variables": variables,
                            "note": f"Variables defined in step: {test_step.name}"
                        }
                        converted_steps.append(converted_step)
                    
                    # Try dispatcher for other types
                    else:
                        logger.info(f"Attempting to convert step using dispatcher: {test_step.name}")
                        context = {
                            "test_suite": test_suite.name,
                            "test_case_name": test_case.name,
                        }
                        
                        try:
                            # Use dispatcher if available
                            result = dispatch_step_conversion(test_step, context)
                            if result:
                                if isinstance(result, list):
                                    for r in result:
                                        if isinstance(r, dict):
                                            r["test_suite"] = test_suite.name
                                            r["test_case"] = test_case.name
                                            converted_steps.append(r)
                                elif isinstance(result, dict):
                                    result["test_suite"] = test_suite.name
                                    result["test_case"] = test_case.name
                                    converted_steps.append(result)
                        except Exception as e:
                            logger.warning(f"Dispatcher failed for step {test_step.name}: {str(e)}")

        # Detect setup and utility test cases
        setup_test_cases = []
        for step in converted_steps:
            case_name = step.get("test_case", "")
            if any(keyword in case_name.lower() for keyword in ["setup", "library", "function", "utility"]):
                if case_name not in setup_test_cases:
                    setup_test_cases.append(case_name)

        # Build Postman collection
        collection = build_postman_collection(
            project_name,
            converted_steps,
            setup_test_cases=setup_test_cases,
            api_endpoints=api_endpoints
        )

        # Write collection to file
        with open(output_file, 'w') as f:
            json.dump(collection, f, indent=2)
        logger.info(f"Postman collection written to {output_file}")

        # Create environment file if requested
        if env_file:
            # Create generic environment variables
            env_vars = [
                {
                    "key": "baseUrl",
                    "value": "https://api.example.com",
                    "type": "default",
                    "enabled": True
                },
                {
                    "key": "path",
                    "value": "/api/v1",
                    "type": "default",
                    "enabled": True
                },
                {
                    "key": "username",
                    "value": "",
                    "type": "default",
                    "enabled": True
                },
                {
                    "key": "password",
                    "value": "",
                    "type": "secret",
                    "enabled": True
                },
                {
                    "key": "apiKey",
                    "value": "",
                    "type": "secret",
                    "enabled": True
                },
                {
                    "key": "token",
                    "value": "",
                    "type": "secret",
                    "enabled": True
                },
                {
                    "key": "sessionId",
                    "value": "",
                    "type": "default",
                    "enabled": True
                },
                {
                    "key": "cardNumber",
                    "value": "",
                    "type": "secret",
                    "enabled": True
                },
                {
                    "key": "authToken",
                    "value": "",
                    "type": "secret",
                    "enabled": True
                },
                {
                    "key": "id",
                    "value": "",
                    "type": "default",
                    "enabled": True
                }
            ]
            
            # Generate environment with a unique ID
            environment = {
                "id": str(uuid.uuid4()),
                "name": f"{project_name}_Environment",
                "values": env_vars
            }
            
            with open(env_file, 'w') as f:
                json.dump(environment, f, indent=2)
            logger.info(f"Postman environment written to {env_file}")
            print(f"✅ Environment file created: {env_file}")

        print(f"\n✅ Conversion completed. Output saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        raise


# Entry point
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ReadyAPI project XML to Postman collection')
    parser.add_argument('--input', required=True, help='Path to ReadyAPI project XML')
    parser.add_argument('--output', required=True, help='Path to output Postman collection JSON file')
    parser.add_argument('--env', help='Path to output Postman environment JSON file')
    args = parser.parse_args()

    run_readyapi_to_postman(args.input, args.output, args.env)
