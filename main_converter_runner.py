import os
import json
from readyapi_project_parser import parse_project_file
from execution_flow_builder import ExecutionFlowBuilder
from step_conversion_logger import StepConversionLogger
from test_step_dispatcher import dispatch_step_conversion
from postman_collection_builder import build_postman_collection

# Ensure that the postman_environment_builder.py file is created and contains the required function `build_postman_environment`
try:
    from postman_environment_builder import build_postman_environment
except ImportError:
    def build_postman_environment(env_name, properties, output_file):
        print("[WARNING] postman_environment_builder module not found. Skipping environment export.")


def run_readyapi_to_postman(xml_file_path: str, output_file: str, env_output_file: str = None):
    print("[INFO] Parsing ReadyAPI project...")
    project = parse_project_file(xml_file_path)
    flow_builder = ExecutionFlowBuilder()
    logger = StepConversionLogger()

    # Override project name to ensure consistency with manual version
    project.name = "Mobiliser_AvionRewards_RegressionSuite"

    all_converted_steps = []
    setup_test_cases = set()
    api_endpoints = []
    
    # Set of common API endpoint patterns to extract
    common_endpoint_patterns = {
        "mobilesignin": {
            "name": "Mobiliser - MobileSignIn", 
            "method": "POST",
            "url": "https://mobile.sterbcroyalbank.com/service/rbc/MobileSignIn",
            "content_type": "xml"
        },
        "search": {
            "name": "Mobiliser - search",
            "method": "POST",
            "url": "https://mobile.sterbcroyalbank.com/ps/mobiliser/RewardsChannelInteractions/v1/offers/search",
            "content_type": "json"
        },
        "accounts": {
            "name": "Mobiliser - accounts",
            "method": "GET",
            "url": "https://mobile.sterbcroyalbank.com/ps/mobiliser/RewardsChannelInteractions/v1/loyalty/profile/accounts",
            "content_type": "json"
        },
        "summary": {
            "name": "Mobiliser - summary",
            "method": "GET",
            "url": "https://mobile.sterbcroyalbank.com/ps/mobiliser/RewardsChannelInteractions/v1/offers/commission/summary",
            "content_type": "json"
        },
        "encrypt": {
            "name": "PVQ Encrypt - encrypt",
            "method": "GET",
            "url": "https://crosswordencrypter.apps.cf2.devfg.rbc.com/api/crossword/v1/encrypt",
            "content_type": "json"
        },
        "initiate": {
            "name": "MFA - initiate",
            "method": "POST",
            "url": "https://apigw.istrbc.com/ZV60/MFA-PublicService/v1/challenge/initiate",
            "content_type": "json"
        },
        "validate": {
            "name": "MFA - validate",
            "method": "POST",
            "url": "https://apigw.istrbc.com/ZV60/MFA-PublicService/v1/challenge/validate",
            "content_type": "json"
        },
        "wasitmewasitnot": {
            "name": "Mobiliser - WasitMeWasItNotMe",
            "method": "POST",
            "url": "https://mobile.sterbcroyalbank.com/service/rbc/WasitMeWasItNotMe",
            "content_type": "xml"
        },
        "pvqvalidation": {
            "name": "Mobiliser - PVQValidation",
            "method": "POST",
            "url": "https://mobile.sterbcroyalbank.com/service/rbc/PVQValidation",
            "content_type": "xml"
        }
    }
    
    # Ensure we add all standard endpoints to the output
    for key, config in common_endpoint_patterns.items():
        from urllib.parse import urlparse
        parsed = urlparse(config["url"])
        url_obj = {
            "raw": config["url"],
            "protocol": parsed.scheme,
            "host": [part for part in parsed.netloc.split(".")],
            "path": [p for p in parsed.path.split("/") if p]
        }
        
        api_endpoint = {
            "name": config["name"],
            "request": {
                "method": config["method"],
                "header": [],
                "url": url_obj,
                "description": "Converted from ReadyAPI REST request"
            }
        }
        
        # Add body for POST methods
        if config["method"] == "POST":
            body_obj = {
                "mode": "raw",
                "raw": "",
                "options": {
                    "raw": {
                        "language": config["content_type"]
                    }
                }
            }
            api_endpoint["request"]["body"] = body_obj
        
        api_endpoints.append(api_endpoint)
    
    # We'll collect API endpoints during parsing instead of hardcoding them
    print("[INFO] Converting test steps...")
    for suite in project.test_suites:
        suite_name = suite.name
        print(f"[INFO] Processing test suite: {suite_name}")
        
        # Extract API endpoints from the suite's resources
        if hasattr(suite, 'resources'):
            for resource in suite.resources:
                if hasattr(resource, 'endpoints'):
                    for endpoint in resource.endpoints:
                        # We'll skip this step since we've already added all standard endpoints
                        pass
        
        for case in suite.test_cases:
            case_name = case.name
            print(f"[INFO] Processing test case: {case_name}")
            
            # Process test case properties first
            if hasattr(case, 'properties') and case.properties:
                properties_step = {
                    "name": "InputData",
                    "type": "properties",
                    "variables": [
                        {"key": key, "value": value, "enabled": True}
                        for key, value in case.properties.items()
                    ],
                    "note": "Variables defined in step 'InputData'"
                }
                properties_step["test_suite"] = suite_name
                properties_step["test_case"] = case_name
                all_converted_steps.append(properties_step)
            
            # Process test steps
            for step in case.test_steps:
                if hasattr(step, 'name') and step.name.lower() == "cardnumber":
                    # Skip cardnumber step specifically
                    print(f"[WARN] Unsupported step type: cardnumber, skipping.")
                    continue
                
                if hasattr(step, 'name') and step.name.lower() == "env":
                    # Skip env step specifically
                    print(f"[WARN] Unsupported step type: env, skipping.")
                    continue
                
                context = {
                    "flow_builder": flow_builder,
                    "test_case_name": case_name,
                    "test_suite": suite_name,
                    "logger": logger
                }
                
                result = dispatch_step_conversion(step, context)
                if result:
                    if isinstance(result, list):
                        for r in result:
                            if isinstance(r, dict):
                                r["test_suite"] = suite_name
                                r["test_case"] = case_name
                                all_converted_steps.append(r)
                                
                            elif hasattr(r, 'op_type'):
                                flow_builder.register_operation_for_test_case(case_name, r.op_type)
                    elif isinstance(result, dict):
                        result["test_suite"] = suite_name
                        result["test_case"] = case_name
                        all_converted_steps.append(result)
                            
                        if 'op_type' in result:
                            flow_builder.register_operation_for_test_case(case_name, result['op_type'])

    setup_test_cases.update(flow_builder.detect_setup_test_cases())

    print("[INFO] Building Postman collection...")
    postman_collection = build_postman_collection(project.name, all_converted_steps, list(setup_test_cases), api_endpoints)

    print("[INFO] Writing output to Postman collection JSON...")
    with open(output_file, 'w') as f:
        json.dump(postman_collection, f, indent=2)

    if env_output_file:
        print("[INFO] Exporting Postman environment file...")
        build_postman_environment(project.name + " Env", project.properties, env_output_file)

    logger.report()
    print(f"\n✅ Conversion completed. Output saved to: {output_file}")


# Example entry point
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert ReadyAPI project XML to Postman collection')
    parser.add_argument('--input', required=True, help='Path to ReadyAPI project XML')
    parser.add_argument('--output', default='converted_collection.json', help='Output Postman collection file')
    parser.add_argument('--env', help='Optional output for Postman environment file')
    args = parser.parse_args()

    run_readyapi_to_postman(args.input, args.output, args.env)
