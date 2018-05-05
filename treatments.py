import os
import subprocess
import json
import ast


def lookupID(name):

    # Lookup entity ID given synonym
    limit = 10   # Results limit
    cmd = ["curl", "-X", "GET", "-k", "-uhackathon:4wxQ82cgxrSey8", "--header",
        "Accept: application/json",
        "https://demods12.scibite.com/api/entity/v1/lookup/id?syn="+str(name)+"&type=DRUG&limit="+str(limit)]

    output = subprocess.Popen( cmd, stdout=subprocess.PIPE).communicate()[0]    # Run above command in terminal
    output_str = str(output)        # Convert to string
    output_str = output_str[10:-3]  # Remove unnecessary parts of output

    return output_str


def matrixQuery(id1, id2):

    # Generate Scbite ID for query
    Scibite_ID = str(id1)+"$"+str(id2)
    # Lookup entity ID given synonym
    limit = 10  # Results limit
    cmd = ["curl", "-X", "GET", "-k", "-uhackathon:4wxQ82cgxrSey8", "--header",
        "Accept: application/json",
        "https://demods12.scibite.com/api/ds/v1/lookup/matrix/medline/*/*/*?fields=*&query=id:"+str(Scibite_ID)+"&filter=INDICATION&limit="+str(limit)+"&from=0&scibiteranking=false&useSentenceCC=false&adduids=true&zip=false"]

    output = subprocess.Popen( cmd, stdout=subprocess.PIPE).communicate()[0]    # Run above command in terminal
    output_str = str(output)        # Convert to string
    output_str = output_str[2:-1]     # Remove unnecessary parts of output
    output_str = output_str.replace('\\n', '')

    return output_str


### Main ###
drug_info_dict = {}
synonym = 'viagra'

# Lookup initial ID info for disease
ID_info = lookupID(synonym)
ID_info_dict = ast.literal_eval(ID_info)
drug_info_dict.update(ID_info_dict)

# Lookup disease info from ID
query_info = matrixQuery(ID_info_dict['type'], ID_info_dict['id'])
query_info_dict = ast.literal_eval(query_info)

drug_info_dict["diseases"] = {}
facets = query_info_dict["facets"]

# Add all diseases and counts to dict
for facet in facets:
    label = facet["label"].split('$')
    key = str(label[-1])
    value = int(facet["count"])
    drug_info_dict["diseases"].update({key:value})

# Write to JSON
#j = json.dumps(drug_info_dict)
with open('data.json', 'w') as outfile:
    outfile.write('data = ')
    json.dump(drug_info_dict, outfile)

