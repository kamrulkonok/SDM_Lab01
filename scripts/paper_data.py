import requests
import time
import csv

url = "https://api.semanticscholar.org/graph/v1/paper/search"

headers = {
    'x-api-key': 'QBCOvr5LpG5R231Hcyc5a1wYmv3kltNy40sKfufK'
}

def get_papers_data(query, limit, fields):
    query_params = {
        'query': query,
        'limit': limit,
        'fields': fields,
        'year': '2015-', 
        'offset': 0 
    }
    papers_data = []

    while len(papers_data) < limit:
        response = requests.get(url, headers=headers, params=query_params)
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            break

        data = response.json()
        papers = data.get('data', [])

        for paper in papers:
            journal_data = paper.get('journal', None)
            journal_name = journal_data.get('name') if journal_data else None
            journal_volume = journal_data.get('volume') if journal_data else None
            journal_pages = journal_data.get('pages') if journal_data else None
            
            paper_data = {
                'paperId': paper.get('paperId'),
                'title': paper.get('title'),
                'url': paper.get('url'),
                'venue': paper.get('venue', {}).get('name') if isinstance(paper.get('venue'), dict) else paper.get('venue'),
                'publicationTypes': paper.get('publicationTypes'),
                'abstract': paper.get('abstract'),
                'year': paper.get('year'),
                'citationCount': paper.get('citationCount'),
                'journal': {
                    'name': journal_name,
                    'volume': journal_volume,
                    'pages': journal_pages
                }
            }
            papers_data.append(paper_data)
        if 'next' in data:
            query_params['offset'] += limit
        else:
            break
        time.sleep(1)

    return papers_data
fields = 'paperId,title,url,venue,publicationTypes,abstract,year,citationCount,journal'

fields_queries = ['NLP','Machine Learning','LLM', 'Deep Learning', 'Quantum Computing', 'Graph Database',  'Data Management', 'Indexing', 'Data Modeling',' Big Data', 'Data Processing', 'Data Storage', 'Data Querying']
all_papers_data = {}

for field_query in fields_queries:
    all_papers_data[field_query] = get_papers_data(field_query, 100, fields)
    time.sleep(1)
headers = [
    'field_query', 'paperId', 'title', 'url', 'venue', 'publicationTypes',
    'abstract', 'year', 'citationCount', 'journal_name', 'journal_volume', 'journal_pages'
]
with open('papers_data.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=headers)
    writer.writeheader()
    for field_query, papers in all_papers_data.items():
        for paper in papers:
            journal_data = paper['journal']
            writer.writerow({
                'field_query': field_query,
                'paperId': paper['paperId'],
                'title': paper['title'],
                'url': paper['url'],
                'venue': paper['venue'],
                'publicationTypes': paper['publicationTypes'],
                'abstract': paper['abstract'],
                'year': paper['year'],
                'citationCount': paper['citationCount'],
                'journal_name': journal_data.get('name', ''),
                'journal_volume': journal_data.get('volume', ''),
                'journal_pages': journal_data.get('pages', '')
            })

print('Data has been written to papers_data.csv')