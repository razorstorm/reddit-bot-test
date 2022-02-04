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
        if "min" and "max" in data:
            return f"""
    Min: {data['min']}
    Max: {data['max']}
            """
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
            name
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
            #   print(response["data"])
            #We loop through the response, objects
            for subs in response["data"]["substances"]:
                print(f"Name: {drug_name} {subs['name']}")
                #print name
                #   print(f"Name: {subs['name']}")
                #print summary
                #   print(f"Summary: {subs['summary']}")

                #print dosage information
                #   print("Doses:")
                #   doses = subs['roas'][0]['dose']
                #   if doses:
                #     print(f"Common {expand(doses['common'])}")
                #     print(f"Heavy {doses['heavy']}")
                #     print(f"Light {expand(doses['light'])}")
                #     print(f"Strong {expand(doses['strong'])}")
                #     print(f"Threshold { doses['threshold']}")
                #     print(f"Units {doses['units']}")
                #     print("")

                #   #print duration information
                #   duration = subs['roas'][0]['duration']
                #   if duration:
                #     print(f"Afterglow {expand(duration['afterglow'])}")
                #     print(f"Comeup {expand(duration['comeup'])}")
                #     print(f"Duration {expand(duration['duration'])}")
                #     print(f"Offset {expand(duration['offset'])}")
                #     print(f"Onset {expand(duration['onset'])}")
                #     print(f"Peak {expand(duration['peak'])}")
                #     print(f"Total {expand(duration['total'])}")
        #If we instead run into an "error" then there was an error in the request
        elif "error" in response:
            print("There was an error in the API Request!!")
            return None
        
        return None
