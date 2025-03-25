import sys
import os
import json
import requests
from simple_salesforce import Salesforce

# Add the path to the sfPyAuth module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs', 'sfPyAuth', 'src'))

from sfPyAuth.sfPyAuth import oAuthController

sfAuth = oAuthController()
# sfInstance = Salesforce(instance_url=sfAuth.sf_instanceUrl, session_id=sfAuth.accessToken)

# Test Mode (Syncronous or ASync)
# testMode : str = "runTestsSynchronous"
testMode : str = "runTestsAsynchronous"

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
    query :str = "SELECT+Id,ApexClassOrTriggerId,ApexClassOrTrigger.name,TestMethodName,Coverage+from+ApexCodeCoverage"
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


def main():
    """
    Main function to orchestrate fetching test classes, executing them, and retrieving coverage.
    """
    testClasses = getTestClasses()
    if testClasses == None:
        print("No Test Classes Found")
        os._exit(1)
    
    testRunId : str = executeTestClasses(testClasses)
    
    if testRunId == None:
        print("Error running tests")
        os._exit(1)
        
    # waitForTest(testRunId)
    
    getCoverage()
        
    print("Pause here for debugging!")
    
    

if __name__ == "__main__":
    main()