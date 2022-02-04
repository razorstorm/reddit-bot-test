# This is the API we need to POST too..
# https://api.psychonautwiki.org/
#

import requests
import json

#HTTP Headers we send to the server
headers = {
    "accept-type": "application/json",
    "content-type": "application/json"
}


#Small function that check if the object has "min" and "max" and if so, return both as a single string object.
def expand(data):
    try:
        units = None
        if "units" in data:
            units = data["units"]
        if "min" and "max" in data:
            return f"{data['min']} - {data['max']} {units}"
    except:
        #if nothing is passed in, then no information is returned
        if data == None:
            return "No information"
        #otherwise we just pass teh data sent, good for if the response is just an int or a string.
        else:
            return data

def lookup(drug_name):
    #JSON string sent to the server
    # This is a formated string, the %s acts as a placeholder for the variable at the end
    payload = {
        "query": """
    {
        substances(query: "%s") {
            name url
            summary
            # routes of administration
            roas {
                name
                dose {
                    units
                    threshold
                    heavy
                    common { min max }
                    light { min max }
                    strong { min max }
                }
                duration {
                    afterglow { min max units }
                    comeup { min max units }
                    duration { min max units }
                    offset { min max units }
                    onset { min max units }
                    peak { min max units }
                    total { min max units }
                }
            }
        }
    }
        """ % drug_name #is used when replacing the %s above.
    }

    #Convert dictionary object into a JSON string (required for sending to the server)
    json_payload = json.dumps(payload)

    #Create a POST request to the server
    api = requests.post("https://api.psychonautwiki.org/?",data=json_payload,headers=headers)

    #If the request was sent
    if api:
        #We convert the response text into a JSON object, that contains the response data.
        response = json.loads(api.text)

        #We check for a "data" object in the response, this is standard response for proper results
        if "data" in response:
            return response["data"]["substances"]
        #If we instead run into an "error" then there was an error in the request
        elif "error" in response:
            print("There was an error in the API Request!!")
            return None
        
        return None
