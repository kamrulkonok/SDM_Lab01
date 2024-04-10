from neo4j import GraphDatabase
from load_config import load_config

class GraphDatabaseService:
    def __init__(self, config):
        self.driver = GraphDatabase.driver(
            config["uri"], 
            auth=(config["user"], config["password"])
        )

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]
#Query 01: Find the top 3 most cited papers of each conference.
    def find_top_cited_papers_by_conference(self):
        query = """
        MATCH (p:Paper) - [r1:CITES] -> (citedPaper:Paper) - [r2:PUBLISHED_IN] -> (c:Conference) 
        WITH c, citedPaper, COUNT(r1) AS numberOfCitations
        ORDER BY c, numberOfCitations DESC
        WITH c, COLLECT(citedPaper)[0..3] AS top3
        WHERE SIZE(top3) > 2 AND NONE(x IN top3 WHERE x.title = 'None')
        RETURN c.name as conference, 
               top3[0].title AS topCitedPaper1,
               top3[1].title AS topCitedPaper2,
               top3[2].title AS topCitedPaper3
        """
        results = self.execute_query(query)
        print("Top 3 most cited papers by conference:")
        for record in results:
            print(f'{record["conference"]}: {record["topCitedPaper1"]}, {record["topCitedPaper2"]}, {record["topCitedPaper3"]}')
# Query 02: For each conference find its community: i.e., those authors that have published papers on that conference in, at least, 4 different editions.
    def find_conference_communities(self):
        query = """
        MATCH (a:Author)-[:WROTE]->(p:Paper)-[pin:PUBLISHED_IN]->(c:Conference)
        WITH c.name as conferenceName, a, COUNT(DISTINCT pin.edition) AS distinctEditions
        WHERE distinctEditions >= 4
        WITH conferenceName, COLLECT(a.name) AS community
        RETURN conferenceName, community
        """
        results = self.execute_query(query)
        print("Conference communities (authors with papers in >= 4 editions):")
        for record in results:
            print(f'{record["conferenceName"]}: {record["community"]}')

#Query 03: Find the impact factors of the journals in your graph
    def calculate_journal_impact_factor(self):
        query = """
    MATCH (j:Journal)
    WITH j.name AS journalName, 2023 AS year
    OPTIONAL MATCH (last_p:Paper)-[last:PUBLISHED_IN]->(j:Journal{name:journalName})
    WHERE toInteger(last.year) IN [toInteger(year - 1), toInteger(year - 2)]
    WITH journalName, year, COLLECT(last_p.paperId) AS paperIds, size(COLLECT(last_p.paperId)) AS numPaperPublished_last2yrs
    UNWIND paperIds AS paperId
    WITH journalName, year, paperId, numPaperPublished_last2yrs
    MATCH (p1:Paper)-[:CITES]->(p2:Paper{paperId:paperId})
    MATCH (p1)-[:PUBLISHED_IN{year:year}]->(j:Journal)
    WITH journalName, year, numPaperPublished_last2yrs, count(*) AS numCitations
    RETURN journalName, numCitations / numPaperPublished_last2yrs AS impact_factor
    ORDER BY impact_factor DESC;
        """
        results = self.execute_query(query)
        print("Journal impact factors:")
        for result in results:
            print(f'Journal: {result["journalName"]}, Impact Factor: {result["impact_factor"]}')
#Query 04: Find the h-indexes of the authors in your graph
    def calculate_author_h_index(self):
        query = """
        MATCH (author:Author)-[:WROTE]->(paper:Paper)
        OPTIONAL MATCH (citingPaper:Paper)-[:CITES]->(paper)
        WITH author, paper, COUNT(citingPaper) AS citations
        ORDER BY citations DESC
        WITH author, COLLECT(citations) AS citationCounts
        UNWIND RANGE(1, SIZE(citationCounts)) AS index
        WITH author, citationCounts, index
        WHERE citationCounts[index-1] >= index
        RETURN author.name AS AuthorName, MAX(index) AS HIndex
        ORDER BY HIndex DESC
        """
        results = self.execute_query(query)
        print("Author h-indexes:")
        for result in results:
            print(f'Author: {result["AuthorName"]}, H-Index: {result["HIndex"]}')
if __name__ == "__main__":
    config = load_config()
    graph_db_service = GraphDatabaseService(config)

    try:
        graph_db_service.find_top_cited_papers_by_conference()
        graph_db_service.find_conference_communities()
    finally:
        graph_db_service.close()
