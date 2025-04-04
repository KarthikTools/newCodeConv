from converters.rest_request_converter import convert_rest_request
from converters.datasource_converter import convert_datasource_step
from converters.properties_converter import convert_properties_step
from converters.property_transfer_converter import convert_property_transfer_step
from analyzer.groovy_behavior_classifier import GroovyBehaviorClassifier

from typing import Dict

class StepConversionLogger:
    def __init__(self):
        self.skipped_steps = []
        self.partial_steps = []

    def log_skipped(self, step_name: str, step_type: str, reason: str):
        self.skipped_steps.append({
            "name": step_name,
            "type": step_type,
            "reason": reason
        })

    def log_partial(self, step_name: str, step_type: str, reason: str):
        self.partial_steps.append({
            "name": step_name,
            "type": step_type,
            "reason": reason
        })

    def report(self):
        if self.skipped_steps:
            print("\n⚠️ Skipped Steps:")
            for step in self.skipped_steps:
                print(f"  • {step['name']} ({step['type']}): {step['reason']}")

        if self.partial_steps:
            print("\n⚠️ Partially Converted Steps:")
            for step in self.partial_steps:
                print(f"  • {step['name']} ({step['type']}): {step['reason']}")

STEP_HANDLERS = {
    "restrequest": convert_rest_request,
    "httprequest": convert_rest_request,
    "datasource": convert_datasource_step,
    "properties": convert_properties_step,
    "property-transfer": convert_property_transfer_step,
    "groovy": lambda step, context: GroovyBehaviorClassifier(
        step.config,
        context.get("test_case_name"),
        context.get("flow_builder")
    ).classify(),
}

SUPPORTED_OPTIONAL = {
    "delay", "datasink", "conditional goto", "script assertion", "doc test step"
}

SKIPPED_TYPES = {
    "goto", "mockresponse", "amqp", "jms", "mqtt", "jdbc", "file wait",
    "manual", "soapresponse", "wsdl", "test debug", "loadtest"
}

def dispatch_step_conversion(test_step, context: Dict):
    logger: StepConversionLogger = context.get("logger")
    step_type = test_step.step_type.lower()
    handler = STEP_HANDLERS.get(step_type)

    if handler:
        return handler(test_step, context)
    elif step_type in SUPPORTED_OPTIONAL:
        if logger:
            logger.log_partial(test_step.name, step_type, "Simulated or requires manual script insert in Postman")
        return {
            "type": step_type,
            "note": f"Simulated behavior of optional step '{step_type}' from ReadyAPI"
        }
    elif step_type in SKIPPED_TYPES:
        if logger:
            logger.log_skipped(test_step.name, step_type, "Step type unsupported by Postman environment")
        return None
    else:
        if logger:
            logger.log_skipped(test_step.name, step_type, "Unknown or unhandled step type")
        return None
