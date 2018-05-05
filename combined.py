import os
import subprocess
import json
import ast
import re
import requests

from opentargets import OpenTargetsClient


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


def openTargets2():
    '''
    from opentargets import OpenTargetsClient
    client = OpenTargetsClient()
    response = client.get_associations_for_target('BRAF',
    	fields = ['associations_score.datasource*',
    			'associations_score.overall',
    			'target.gene_info.symbol',
    			'disease.efo_info.*']
    		)
    response.to_excel('BRAF_associated_diseases_by_datasource.xls')
    '''

    client = OpenTargetsClient()
    response = client.get_associations_for_target('ENSG00000157764',
    	fields=['association_score.datasource*','association_score.overall','target.gene_info.symbol','disease.efo_info.*'])
    print(response)


def findDiseases(ddd):
	diseaseList = []
	diseaseCount = []
	a_for_target = ot.get_associations_for_target(ddd)
	for a in a_for_target:
		diseaseList.append(a['disease']['id'])
		diseaseCount.append(a['evidence_count']['datatypes']['literature'])
	return diseaseList, diseaseCount


def generateDiseaseJSON(target):
	diseases = []
	diseaseCounts = []
	diseases, diseaseCounts = findDiseases(target)

	json_data = '{diseases:{'
	for i in range(0,5):
		json_data = json_data + '"' + diseases[i] + '"'+ ':' + '"' + str(diseaseCounts[i]) + '"' + ','
	json_data = json_data[:-1]
	json_data = json_data + '}'
	return(json_data)
	#findSimilarTargets(targets[i])


def mechansim(CHEMBLID):
	parameters =  CHEMBLID
	base = 'https://www.ebi.ac.uk/chembl/api/data/mechanism/'+parameters
	response = requests.get(url = base)

	#a = tree.getroot()
	#print(type(response.content))
	text = str(response.content)
	#print(type(text))
	pos = text.find('<mechanism_of_action>')
	pos1 = text.find('</mechanism_of_action>')
	actionType = text[pos+21:pos1]
	return actionType


##### Main #####

#####################
#       IDs         #
#####################

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

#####################
#   Get Targets     #
#####################



#####################
#  Similar Diseases #
#####################

ot = OpenTargetsClient()
target = 'BRAF'
similarDiseasesJSON = generateDiseaseJSON(target)

#####################
#   Get Action Type #
#####################

CHEMBLID = drug_info_dict["id"].replace('CHEMBL','')
actionType =  mechansim(CHEMBLID)
drug_info_dict.update({"ActionType":actionType})

#####################
#  Write to JSON    #
#####################

with open('data.json', 'w') as outfile:
    # j = json.dumps(drug_info_dict)
    # j_data = 'data='+j
    # json.dump(j_data, outfile)
    outfile.write('data=\"')
    json.dump(drug_info_dict, outfile)
    outfile.write('\"')