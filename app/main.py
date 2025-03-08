from simple_salesforce import Salesforce
from libs.sfPyAuth.src.sfPyAuth.sfPyAuth import oAuthController



sfAuth = oAuthController()
sfInstance = Salesforce(instance_url=sfAuth.sf_instanceUrl, session_id=sfAuth.sm.accessToken)
    
def __init__(self):
    if sfAuth.sm.accessToken == None:
        print("No Access Token. Auth is broken. Exiting.")
        exit(1)

def main():
    result = sfInstance.query("SELECT Id FROM User LIMIT 5")
    print(result)

if __name__ == "__main__":
    main()