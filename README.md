# ReadyAPI to Postman Converter

A tool that converts ReadyAPI test projects to Postman collections, enabling seamless migration of API tests between platforms.

## Overview

This converter takes ReadyAPI project XML files and converts them into Postman collections and environments. It preserves test structure, request details, test scripts, and environment variables.

## Features

- **Complete Test Conversion**: Converts test suites, test cases, and test steps.
- **Script Conversion**: Transforms Groovy scripts into JavaScript for Postman compatibility.
- **Dynamic Endpoint Detection**: Extracts API endpoints from project files.
- **Environment Variables**: Creates environment files with appropriate variables.
- **URL Sanitization**: Properly formats and sanitizes URLs while preserving original paths.
- **Special Step Handling**: Custom handlers for special step types like setup scripts and library functions.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- ReadyAPI XML project files

### Installation

Clone this repository:

```
git clone https://github.com/your-username/ReadyAPI_to_Postman_Converter.git
cd ReadyAPI_to_Postman_Converter
```

### Usage

Run the converter with the following command:

```
python main_converter_runner.py --input /path/to/readyapi/project.xml --output /path/to/output.json --env /path/to/environment.json
```

Arguments:
- `--input`: Path to ReadyAPI project XML file (required).
- `--output`: Path to output Postman collection JSON file (required).
- `--env`: Path to output Postman environment JSON file (optional).

## Architecture

The converter uses a modular architecture to handle different aspects of the conversion process:

- `main_converter_runner.py`: Main entry point that orchestrates the conversion process.
- `readyapi_project_parser.py`: Parses ReadyAPI XML files into Python objects.
- `converters/`: Directory containing specialized converters for different types of test steps.
  - `rest_request_converter.py`: Converts REST API requests.
  - `properties_converter.py`: Converts property steps.
  - Other specialized converters.
- `test_step_dispatcher.py`: Dispatches test steps to appropriate converters.
- `postman_collection_builder.py`: Builds the final Postman collection structure.
- `postman_environment_builder.py`: Builds the Postman environment file.

## Project Structure

```
ReadyAPI_to_Postman_Converter/
├── main_converter_runner.py       # Main entry point
├── readyapi_project_parser.py     # Parses ReadyAPI XML
├── test_step_dispatcher.py        # Dispatches test steps to converters
├── rest_request_converter.py      # Root converter with common functions
├── postman_collection_builder.py  # Builds Postman collections
├── postman_environment_builder.py # Builds Postman environments
├── execution_flow_builder.py      # Handles test execution flow
├── step_conversion_logger.py      # Logging utility
├── converters/                    # Specialized step converters
│   ├── rest_request_converter.py
│   ├── properties_converter.py
│   └── ...
├── analyzer/                      # Analysis modules
│   └── ...
└── input_files/                   # Sample input files
```

## Example

To convert a sample ReadyAPI project:

```
python main_converter_runner.py --input input_files/ready_api_project.xml --output converted_collection.json --env converted_environment.json
```

## Features in Detail

### Dynamic Endpoint Extraction

The converter extracts full endpoint paths from the ReadyAPI project structure, handling various formats and conventions.

### Sanitization

The converter sanitizes sensitive data (like credit card numbers) and properly structures URLs for Postman compatibility.

### Script Conversion

Groovy scripts are converted to JavaScript, with special handling for:
- SetupScriptLibrary
- FunctionLibrary
- InSetup
- RunTest

## Limitations

- Some advanced Groovy script features may need manual adjustments.
- Complex authentication schemes might require additional configuration.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 