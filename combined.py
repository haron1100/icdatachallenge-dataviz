import os
import subprocess
import json
import ast
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
import urllib.request
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

	json_data = '{'
	for i in range(0,5):
		json_data = json_data + '"' + diseases[i] + '"'+ ':' + '"' + str(diseaseCounts[i]) + '"' + ','
	json_data = json_data[:-1]
	json_data = json_data + '}'
	return(json_data)
	#findSimilarTargets(targets[i])


def mechansim(CHEMBLID):
	parameters =  CHEMBLID
	base = 'https://www.ebi.ac.uk/chembl/api/data/mechanism/' + parameters
	response = requests.get(url = base)

	#a = tree.getroot()
	#print(response.content)
	text = str(response.content)
	#print(type(text))
	pos = text.find('<mechanism_of_action>')
	pos1 = text.find('</mechanism_of_action>')

	pos3 = text.find('<target_chembl_id>')
	pos4 = text.find('</target_chembl_id>')

	pos5 = text.find('<ref_url>')
	pos6 = text.find('</ref_url>')

	actionType = text[pos+21:pos1]
	targetChemblid = text[pos3+18:pos4]
	paperURL = text[pos5+9:pos6]
	return actionType,targetChemblid,paperURL


def image(CHEMBLID):
    param = CHEMBLID
    URL = 'https://www.ebi.ac.uk/chembl/api/data/image/CHEMBL'+param

    with urllib.request.urlopen(URL) as url:
        with open('temp.jpg', 'wb') as f:
            f.write(url.read())

    img = Image.open('temp.jpg')

    return img


def getName(target_id):

    url = 'https://www.ebi.ac.uk/chembl/target/inspect/'+target_id

    response = requests.get(url)
    content = str(response.content)

    soup = BeautifulSoup(content, 'lxml')

    out = soup.find_all('table', {'class':'contenttable_lmenu'})

    namesoup = BeautifulSoup(str(out[1]), 'lxml')

    nameout = namesoup.find_all('td')
    name = nameout[3].contents[0].strip('\\n ')
    # print(type(name))
    # print(name)
    return name

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
drug_info_dict["diseases_paper_refs"] = {}
facets = query_info_dict["facets"]

# Add all diseases and counts to dict
for facet in facets:

    # Add disease data
    label = facet["label"].split('$')
    key = str(label[-1])
    value = int(facet["count"])
    drug_info_dict["diseases"].update({key:value})

    drug_info_dict["diseases_paper_refs"].update({key:facet["uids"]})

#####################
#   Get Action Type #
#####################

CHEMBLID = drug_info_dict["id"].replace('CHEMBL','')
actionType, targetChemblid, paperURL =  mechansim(CHEMBLID)

drug_info_dict.update({"ActionType":actionType})
drug_info_dict.update({"TargetChemblID":targetChemblid})
drug_info_dict.update({"TargetPaperURL":paperURL})

target = getName(targetChemblid)

ot = OpenTargetsClient()
similarDiseasesJSON = generateDiseaseJSON(target)

drug_info_dict.update({"Target":target})
drug_info_dict.update({"SimilarDiseases":similarDiseasesJSON})

#####################
#   Write image     #
#####################

img = image(CHEMBLID)

#####################
#  Write to JSON    #
#####################

with open('data.json', 'w') as outfile:
    # j = json.dumps(drug_info_dict)
    # j_data = 'data='+j
    # json.dump(j_data, outfile)
    outfile.write("data=\'")
    json.dump(drug_info_dict, outfile)
    outfile.write("\'")
