import requests

from bs4 import BeautifulSoup


target_id='CHEMBL217'
url = 'https://www.ebi.ac.uk/chembl/target/inspect/'+target_id

response = requests.get(url)
content = str(response.content)

soup = BeautifulSoup(content, 'lxml')

out = soup.find_all('table', {'class':'contenttable_lmenu'})

namesoup = BeautifulSoup(str(out[1]), 'lxml')

nameout = namesoup.find_all('td')
name = nameout[3].contents[0].strip('\\n ')

