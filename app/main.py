import sys
import os
import json
import requests
import argparse

# Add the path to the sfPyAuth module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'sfPyAuth', 'src'))

from sfPyAuth.sfPyAuth import oAuthController

sfAuth = oAuthController()
# sfInstance = Salesforce(instance_url=sfAuth.sf_instanceUrl, session_id=sfAuth.accessToken)

# Test Mode (Syncronous or ASync)
# testMode : str = "runTestsSynchronous"
testMode : str = "runTestsAsynchronous"

# Test Class Execution
# If false, test classes will not be executed. Only coverage will be fetched, based on previous test runs.
executeTests : bool = False

def __init__(self):
    if sfAuth.accessToken == None:
        print("No Access Token. Auth is broken. Exiting.")
        exit(1)


def getTestClasses():
    """
    Fetches all Apex test classes from Salesforce.
    Returns a dictionary of test class names and their details.
    """
    url = "https://mindful-raccoon-234rlq-dev-ed.trailblaze.my.salesforce.com/services/data/v62.0/queryAll/?q=SELECT+Id,Name,Body+FROM+ApexClass+WHERE+NamespacePrefix=null"

    payload = {}
    headers = {
    'Authorization': f'Bearer {sfAuth.accessToken}',
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    jsonRespone = response.json()
    
    testClasses : dict = {}
    
    if jsonRespone["totalSize"] > 0:
        for record in jsonRespone["records"]:
            if record["Body"].find("@isTest") == -1:               
                continue           

            testClass = {
                "Id": record["Id"],
                "Name": record["Name"]
            }
            testClasses[record["Name"]] = testClass
                
    else:
        print("No Test Classes Found")
        return None
    
    return testClasses

def executeTestClasses(testClasses):
    """
    Executes the provided test classes in Salesforce.
    Returns the test run ID if successful.
    """
    url = f"{sfAuth.sf_instanceUrl}/services/data/v62.0/tooling/{testMode}"
    
    payload = parseTestClassesForExecution(testClasses)

    headers = {
        'Authorization': f'Bearer {sfAuth.accessToken}',
        'Content-Type': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    testRunId : str = response.json()
    
    return testRunId
    
    
def parseTestClassesForExecution(testClasses):
    """
    Parses the test classes into the required format for execution.
    Returns the JSON payload as a string.
    """
    parsedTestClasses : dict = {"tests": []}
    
    for testClass in testClasses:
        parsed = { "className" : testClass }
        parsedTestClasses["tests"].append(parsed)
    
    return json.dumps(parsedTestClasses)

def waitForTest(testRunId):
    """
    Waits for the test execution to complete and fetches the test results. Not sure if we will use this yet.
    """
    url = f"{sfAuth.sf_instanceUrl}/services/data/v62.0/tooling/query/?q=SELECT+Id,ApexClassId,MethodName,Outcome,StackTrace+FROM+ApexTestResult+WHERE+AsyncApexJobId='{testRunId}'"
    
    payload = {}
    headers = {
        'Authorization': f'Bearer {sfAuth.accessToken}',
    }
    
    response = requests.request("GET", url, headers=headers, data=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    testResults = response.json()
    
    for result in testResults["records"]:
        print(f"Test: {result['ApexClassId']} - {result['MethodName']} - {result['Outcome']}")
    
    return

def getCoverage():
    """
    Fetches the code coverage details from Salesforce.
    Returns the coverage results as a JSON object.
    """
    query :str = "SELECT+Id,ApexClassOrTriggerId,ApexClassOrTrigger.name,TestMethodName,Coverage+FROM+ApexCodeCoverage"
    url = f"{sfAuth.sf_instanceUrl}/services/data/v62.0/tooling/query/?q={query}"
    
    payload = {}
    headers = {
        'Authorization': f'Bearer {sfAuth.accessToken}',
    }
    
    response = requests.request("GET", url, headers=headers, data=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    coverageResults = response.json()

    return coverageResults

def parseCodeCoverage(fullCodeCoverage):
    """
    Parses the full code coverage results into a dictionary by test class.
        
    Returns the coverage results as a dictionary.
    """
    parsedCoverage : dict = {}
    
    for record in fullCodeCoverage["records"]:
        name : str = record["ApexClassOrTrigger"]["Name"]
        recordId : str = record["ApexClassOrTriggerId"]
        type : str = parse_type(record['ApexClassOrTrigger']['attributes']['url'])
        coveredLines : list = record["Coverage"]["coveredLines"]
        uncoveredLines : list = record["Coverage"]["uncoveredLines"]
        
        
        if len(parsedCoverage) > 0 and parsedCoverage.get(name) != None:
            existingCoverage : dict = parsedCoverage[name]
            coveredLines = dedupeLines(existingCoverage["coverage"]["coveredLines"]["lines"], coveredLines)
            uncoveredLines = dedupeLines(existingCoverage["coverage"]["uncoveredLines"]["lines"], uncoveredLines)
            uncoveredLines = removeCoveredLines(coveredLines, uncoveredLines)
        
        parsedObject : dict = parsedCodeCoverage_dictHelper(name, recordId, coveredLines, uncoveredLines, type)
        
        parsedCoverage.update(parsedObject) # if this dosent work, we will need seperate put and update lines depending on if we update updating or inserting.
        
    return parsedCoverage

def parse_type(url):
    """
    Parses the type of the Apex class or trigger from the URL.
    """
    if url.find("ApexClass") != -1:
        return "ApexClass"
    elif url.find("ApexTrigger") != -1:
        return "ApexTrigger"
    else:
        return "Unknown"

def dedupeLines(coveredLines_existing : list, coveredLines_New : list):
    """
    Dedupes the covered lines between two sets of covered lines.
    """
    return list(set(coveredLines_existing + coveredLines_New))

def removeCoveredLines(coveredLines :list , uncoveredLines : list):
    """
    Removes the covered lines from the uncovered lines.
    """
    return list(set(uncoveredLines) - set(coveredLines))
    

def parsedCodeCoverage_dictHelper(name, recordId, coveredLines, uncoveredLines, type):
    """
    Helper function to parse the code coverage results into a dictionary.
    """
    totalLines : int = len(coveredLines) + len(uncoveredLines)    
    percentage : float = (len(coveredLines) / totalLines) * 100
    parsed : dict = {
            name: {
                "Id": recordId,
                "type": type,
                "coverage": 
                    {
                        "coveredLines": {
                            "lines" : coveredLines,
                            "length" : len(coveredLines)
                        },  
                        "uncoveredLines": {
                            "lines" : uncoveredLines,
                            "length" : len(uncoveredLines)
                        },
                        "coveragePercentage": percentage,
                        "uncoveredPercentage": 100 - percentage
                    }
            }                        
        }
    
    return parsed

def totalCoverage(parsedCodeCoverage):
    """ calculates the total code coverage for all classes """
    
    coveredLines_total : int = 0
    uncoveredLines_total : int = 0
    
    for key in parsedCodeCoverage:
        coveredLines_total += parsedCodeCoverage[key]["coverage"]["coveredLines"]["length"]
        uncoveredLines_total += parsedCodeCoverage[key]["coverage"]["uncoveredLines"]["length"]
    
    totalLines : int = coveredLines_total + uncoveredLines_total
    calculatedCoverage_total :float = (coveredLines_total / totalLines) * 100
    
    orgCoverage_provided : float = getTotalOrgCoverage()
    parsedCodeCoverage.update({"TotalCoverage": calculatedCoverage_total, "OrgCoverage": orgCoverage_provided})
    
    return parsedCodeCoverage    
    
    
def getTotalOrgCoverage():
    query :str = "SELECT+PercentCovered+FROM+ApexOrgWideCoverage"
    url = f"{sfAuth.sf_instanceUrl}/services/data/v62.0/tooling/query/?q={query}"
    
    payload = {}
    headers = {
        'Authorization': f'Bearer {sfAuth.accessToken}',
    }
    
    response = requests.request("GET", url, headers=headers, data=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    responseJson = response.json()
    
    return responseJson['records'][0]['PercentCovered']

def parse_arguments():
    """
    Parses command-line arguments to configure script behavior.
    """
    parser = argparse.ArgumentParser(description="Script to fetch and execute Salesforce test classes.")
    parser.add_argument(
        "--execute-tests",
        type=bool,
        nargs="?",
        const=True,
        help="Set to True to execute test classes, False to only fetch coverage. If not provided, uses the default value."
    )
    args = parser.parse_args()
    return args

def main():
    """
    Main function to orchestrate fetching test classes, executing them, and retrieving coverage.
    """
    global executeTests
    args = parse_arguments()
    if args.execute_tests is not None:
        executeTests = args.execute_tests

    if executeTests:
        testClasses = getTestClasses()
        if testClasses is None:
            print("No Test Classes Found")
            os._exit(1)
        
        testRunId : str = executeTestClasses(testClasses)
        
        if testRunId is None:
            print("Error running tests")
            os._exit(1)
            
        # waitForTest(testRunId)
    
    fullCodeCoverage : dict = getCoverage()
    
    parsedCodeCoverage : dict = parseCodeCoverage(fullCodeCoverage)
    parsedCodeCoverage = totalCoverage(parsedCodeCoverage)
            
    with open("coverage.json", "w") as f:
        json.dump(parsedCodeCoverage, f)
        
    print("Pause here for debugging!")    

if __name__ == "__main__":
    main()