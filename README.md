# Salesforce Code Coverage Tool

This project is a Python-based tool for interacting with Salesforce to fetch Apex test classes, execute them, and retrieve code coverage details. It provides detailed insights into code coverage and generates a JSON report.

## Features

- Fetch Apex test classes from Salesforce.
- Execute test classes synchronously or asynchronously.
- Retrieve detailed code coverage results.
- Parse and calculate total code coverage.
- Generate a JSON report with coverage details.

## Prerequisites

- Python 3.8 or higher.
- Salesforce credentials with API access.
- Required Python libraries:
  - `requests`

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd sfCodeCoverage
   ```

2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure the `sfPyAuth` library is available in the `libs/sfPyAuth/src` directory.

## Configuration

- Update the `oAuthController` in `sfPyAuth` to handle Salesforce authentication.
- Ensure the `sf_instanceUrl` and `accessToken` are correctly set after authentication.

## Usage

1. Run the main script:
   ```bash
   python app/main.py
   ```

2. The script will:
   - Fetch test classes.
   - Execute the tests.
   - Retrieve and parse code coverage.
   - Save the results to `coverage.json`.

3. Check the `coverage.json` file for detailed coverage results.

## Key Functions

- `getTestClasses()`: Fetches all Apex test classes.
- `executeTestClasses(testClasses)`: Executes the provided test classes.
- `getCoverage()`: Retrieves code coverage details.
- `parseCodeCoverage(fullCodeCoverage)`: Parses and organizes coverage data.
- `totalCoverage(parsedCodeCoverage)`: Calculates total coverage percentage.

## Output

- The script generates a `coverage.json` file containing:
  - Coverage details for each class or trigger.
  - Total coverage percentage.
  - Organization-wide coverage percentage.

## To Do

- Have the script wait for the tests to execute. Started working on this but put it aside for now.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](./LICENSE.md) file for details.