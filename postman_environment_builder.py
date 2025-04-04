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
    def build_postman_environment(env_name: str, properties: dict, output_file: str):
        """
        Build a Postman environment file from ReadyAPI project properties
        """
        environment = {
            "id": "pm-env-" + env_name.lower().replace(" ", "-"),
            "name": env_name,
            "values": [],
            "_postman_variable_scope": "environment",
            "_postman_exported_at": "",
            "_postman_exported_using": "ReadyAPI to Postman Converter"
        }

        for key, value in properties.items():
            environment["values"].append({
                "key": key,
                "value": value,
                "enabled": True,
                "type": "default"
            })

        with open(output_file, 'w') as f:
            json.dump(environment, f, indent=2)
        
        print(f"✅ Environment file created: {output_file}")
        return environment


def run_readyapi_to_postman(xml_file_path: str, output_file: str, env_output_file: str = None):
    print("[INFO] Parsing ReadyAPI project...")
    project = parse_project_file(xml_file_path)
    flow_builder = ExecutionFlowBuilder()
    logger = StepConversionLogger()

    all_converted_steps = []
    setup_test_cases = set()

    print("[INFO] Converting test steps...")
    for suite in project.test_suites:
        for case in suite.test_cases:
            for step in case.test_steps:
                context = {
                    "flow_builder": flow_builder,
                    "test_case_name": case.name,
                    "logger": logger
                }
                result = dispatch_step_conversion(step, context)
                if isinstance(result, list):  # for groovy which may return multiple ops
                    for r in result:
                        flow_builder.register_operation_for_test_case(case.name, r.op_type)
                elif isinstance(result, dict):
                    all_converted_steps.append(result)

    setup_test_cases.update(flow_builder.detect_setup_test_cases())

    print("[INFO] Building Postman collection...")
    postman_collection = build_postman_collection(project.name, all_converted_steps, list(setup_test_cases))

    print("[INFO] Writing output to Postman collection JSON...")
    with open(output_file, 'w') as f:
        json.dump(postman_collection, f, indent=2)

    if env_output_file:
        print("[INFO] Exporting Postman environment file...")
        build_postman_environment(project.name + " Env", project.properties, env_output_file)

    logger.report()
    print(f"\n Conversion completed. Output saved to: {output_file}")


# Example entry point
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert ReadyAPI project XML to Postman collection')
    parser.add_argument('--input', required=True, help='Path to ReadyAPI project XML')
    parser.add_argument('--output', default='converted_collection.json', help='Output Postman collection file')
    parser.add_argument('--env', help='Optional output for Postman environment file')
    args = parser.parse_args()

    run_readyapi_to_postman(args.input, args.output, args.env)
