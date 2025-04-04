import json
from typing import List, Dict, Any
import uuid


def build_postman_collection(project_name: str, converted_steps: List[Dict[str, Any]], setup_test_cases: List[str] = None, api_endpoints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a Postman collection from converted ReadyAPI test steps

    Args:
        project_name: The name of the ReadyAPI project
        converted_steps: List of converted test steps
        setup_test_cases: List of test cases that are setup or utility test cases
        api_endpoints: List of API endpoints

    Returns:
        Dict[str, Any]: The Postman collection
    """
    # Use the project name, sanitizing any invalid characters
    collection_name = project_name.replace(" ", "_").strip()
    if not collection_name:
        collection_name = "ReadyAPI_Conversion"
    
    # Remove any trailing underscore
    if collection_name.endswith("_"):
        collection_name = collection_name[:-1]
    
    # Generate a UUID for the collection
    postman_id = str(uuid.uuid4())
    
    # Extract common URL pattern for baseUrl
    base_url = ""  # Empty default, will be populated if found
    for endpoint in (api_endpoints or []):
        request = endpoint.get("request", {})
        url = request.get("url", {})
        if isinstance(url, dict) and url.get("raw"):
            raw_url = url.get("raw")
            if raw_url and "://" in raw_url:
                url_parts = raw_url.split("/")
                if len(url_parts) >= 3:  # protocol://host
                    base_url_candidate = url_parts[0] + "//" + url_parts[2]
                    if base_url_candidate.startswith("http"):
                        base_url = base_url_candidate
                        break
        elif isinstance(url, str) and url.startswith("http"):
            base_url_parts = url.split("/")
            if len(base_url_parts) > 2:
                base_url = base_url_parts[0] + "//" + base_url_parts[2]
                break
    
    # If no base URL was found, use a placeholder
    if not base_url:
        base_url = "{{baseUrl}}"

    # Basic collection structure - minimal with no hardcoded elements
    collection = {
        "info": {
            "name": collection_name,
            "_postman_id": postman_id,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": base_url,
                "type": "string"
            }
        ]
    }

    # Extract any global scripts from converted steps
    global_scripts = extract_global_scripts(converted_steps)
    if global_scripts:
        collection["event"] = global_scripts

    # Group steps by test suite and test case
    suite_steps = {}
    for step in converted_steps:
        suite_name = step.get("test_suite", "Default Suite")
        case_name = step.get("test_case", "Default Case")
        
        if suite_name not in suite_steps:
            suite_steps[suite_name] = {}
        if case_name not in suite_steps[suite_name]:
            suite_steps[suite_name][case_name] = []
            
        suite_steps[suite_name][case_name].append(step)

    # Build collection structure directly from the grouped steps
    for suite_name, cases in suite_steps.items():
        suite_folder = {
            "name": suite_name,
            "description": f"Test suite: {suite_name}",
            "item": []
        }
        
        for case_name, steps in cases.items():
            case_folder = {
                "name": case_name,
                "description": f"Test case: {case_name}",
                "item": []
            }
            
            # Sort steps - InputData should be first, then setup scripts, then others
            sorted_steps = []
            input_data_steps = [step for step in steps if step.get("type") == "properties" or step.get("name") == "InputData"]
            setup_steps = [step for step in steps if any(keyword in step.get("name", "").lower() for keyword in ["setup", "init", "config"])]
            other_steps = [step for step in steps if step not in input_data_steps and step not in setup_steps]
            
            sorted_steps = input_data_steps + setup_steps + other_steps
            
            for step in sorted_steps:
                if step.get("type") == "properties":
                    # Handle properties step
                    properties_item = {
                        "name": step.get("name", "InputData"),
                        "type": "properties",
                        "variables": step.get("variables", []),
                        "note": step.get("note", f"Variables defined in step '{step.get('name', 'InputData')}'")
                    }
                    case_folder["item"].append(properties_item)
                elif "event" in step:
                    # Handle script steps (already formatted properly)
                    case_folder["item"].append(step)
                else:
                    # Handle request steps
                    request = step.get("request", {})
                    url = request.get("url", "{{baseUrl}}")
                    
                    # Create the item based on step type
                    item = {
                        "name": step.get("name", "Unnamed Request"),
                        "request": {
                            "method": request.get("method", "GET"),
                            "header": request.get("header", []),
                            "url": url if isinstance(url, dict) else {"raw": url, "host": [url], "path": [""]},
                            "description": request.get("description", "Converted from ReadyAPI request")
                        }
                    }
                    
                    # Add body if present
                    if "body" in request:
                        item["request"]["body"] = request["body"]
                    
                    # Add headers from step if present
                    if "header" in step:
                        item["request"]["header"] = step["header"]
                    
                    # Add test script if present
                    if "event" in step:
                        item["event"] = step["event"]
                    elif "test_script" in step:
                        item["event"] = [{
                            "listen": "test",
                            "script": {
                                "type": "text/javascript",
                                "exec": step["test_script"].split("\n") if isinstance(step["test_script"], str) else step["test_script"]
                            }
                        }]
                    
                    case_folder["item"].append(item)
            
            suite_folder["item"].append(case_folder)
        
        collection["item"].append(suite_folder)

    # Add API endpoints section if available
    if api_endpoints:
        api_endpoints_folder = {
            "name": "API Endpoints",
            "description": "Collection of all API endpoints from the ReadyAPI project",
            "item": []
        }
        
        # Add endpoints from the project
        for endpoint in api_endpoints:
            api_endpoints_folder["item"].append(endpoint)
        
        collection["item"].append(api_endpoints_folder)

    return collection


def extract_global_scripts(converted_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract global scripts from converted steps
    No hardcoded scripts - dynamically extract from steps
    """
    global_scripts = []
    prerequest_script_lines = []
    test_script_lines = []
    
    # Look for common pre-request and test script patterns in steps
    for step in converted_steps:
        if "event" in step:
            events = step["event"] if isinstance(step["event"], list) else [step["event"]]
            for event in events:
                if event.get("listen") == "prerequest" and "script" in event:
                    script = event["script"]
                    if "exec" in script and isinstance(script["exec"], list):
                        for line in script["exec"]:
                            if (line.strip() and 
                                "pm.request.headers.add" in line and
                                line not in prerequest_script_lines):
                                prerequest_script_lines.append(line)
                elif event.get("listen") == "test" and "script" in event:
                    script = event["script"]
                    if "exec" in script and isinstance(script["exec"], list):
                        for line in script["exec"]:
                            if (line.strip() and 
                                ("pm.test" in line or "pm.response" in line) and
                                line not in test_script_lines):
                                test_script_lines.append(line)
    
    # Add common scripting elements if we found any
    if prerequest_script_lines:
        prerequest_script_lines = ["// Common pre-request script", ""] + prerequest_script_lines
        global_scripts.append({
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": prerequest_script_lines
            }
        })
    
    if test_script_lines:
        test_script_lines = ["// Common test script", ""] + test_script_lines
        global_scripts.append({
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": test_script_lines
            }
        })
    
    return global_scripts


def streamline_prerequest_script(script: str) -> List[str]:
    """Convert a pre-request script to a more concise version"""
    if not script:
        return []
        
    lines = script.split("\n")
    return [line for line in lines if line.strip()]


def streamline_test_script(script: str) -> List[str]:
    """Convert a test script to a more concise version"""
    if not script:
        return []
        
    lines = script.split("\n")
    return [line for line in lines if line.strip()]


# Example usage
if __name__ == "__main__":
    sample_steps = [
        {
            "name": "Login",
            "request": {
                "method": "POST",
                "url": "https://api.example.com/login",
                "header": [],
                "body": {"mode": "raw", "raw": "{}"},
                "description": "Sample login request"
            },
            "event": {
                "test": "pm.test(\"Status code is 200\", function () { pm.response.to.have.status(200); });"
            }
        }
    ]
    collection = build_postman_collection("API Project", sample_steps, setup_test_cases=["Login"])
    with open("converted_postman_collection.json", "w") as f:
        json.dump(collection, f, indent=2)
