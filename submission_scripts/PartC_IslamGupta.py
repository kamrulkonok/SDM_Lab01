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


    def create_community(self):
        query = "MERGE(c:Community{name:'database'});"
        self.execute_query(query)
        print("Community 'database' ensured.")

    def relate_keywords_to_community(self):
        query = """
        MATCH (k:Keyword)
        WHERE k.text IN ['data management', 'indexing', 'data modeling', 'big data', 'data processing', 'data storage', 'data querying']
        WITH k
        MATCH (c:Community{name:'database'})
        MERGE (k)-[:BELONGS_TO]->(c);
        """
        self.execute_query(query)
        print("Keywords related to 'database' community.")

    def relate_publication_to_community(self):
        query = """
        MATCH (c:Community{name:'database'})<-[:BELONGS_TO]-(k:Keyword)<-[:CONTAINS*1..]-(p:Paper)-[pin:PUBLISHED_IN]->(jc)
        WHERE jc:Journal OR jc:Conference
        WITH jc, count(distinct p) as numOfCommPaper
        MATCH (p2:Paper)-[pin2:PUBLISHED_IN]->(jc2)
        WHERE jc2:Journal OR jc2:Conference AND jc2.name = jc.name
        WITH jc, numOfCommPaper, COUNT(distinct p2) as num_paper
        WHERE (toFloat(numOfCommPaper) / num_paper) >= 0.9
        MATCH (entity {name: jc.name})
        MATCH (dc:Community {name:'database'})
        MERGE (entity)-[:RELATED_TO]->(dc);
        """
        self.execute_query(query)
        print("Publication venues related to 'database' community.")

    def assign_topdbpapers_label(self):
        query = """
        MATCH (p1:Paper)-[:PUBLISHED_IN]->(jc1)-[:RELATED_TO]->(dc:Community {name:'database'})
        WHERE jc1:Journal OR jc1:Conference
        MATCH (p2:Paper)-[:PUBLISHED_IN]->(jc2)-[:RELATED_TO]->(dc:Community {name:'database'})
        WHERE jc2:Journal OR jc2:Conference
        MATCH (p2)-[:CITES]->(p1)
        WITH p1, count(distinct p2) AS citationCount
        ORDER BY citationCount DESC
        LIMIT 100
        SET p1:TopDBPaper;
        """
        self.execute_query(query)
        print("Top DB Paper label assigned.")

    def assign_pot_reviewer(self):
        query = """
        MATCH (p:TopDBPaper)<-[:WROTE]-(a:Author)
        MATCH (c:Community{name:'database'})
        MERGE (a)-[:POT_REVIEWER]-(c);
        """
        self.execute_query(query)
        print("Potential reviewers connected to 'database' community.")

    def assign_guru(self):
        query = """
        MATCH (p:TopDBPaper)<-[:WROTE]-(a:Author), (c:Community{name:'database'})
        WITH a, count(p) as cnt
        WHERE cnt >= 2
        MERGE (a)-[:IS_GURU]->(c);
        """
        self.execute_query(query)
        print("Guru status assigned.")


if __name__ == "__main__":
    config = load_config()
    db_service = GraphDatabaseService(config)

    try:
        db_service.create_community()
        db_service.relate_keywords_to_community()
        db_service.relate_publication_to_community()
        db_service.assign_topdbpapers_label()
        db_service.assign_pot_reviewer()
        db_service.assign_guru()
    finally:
        db_service.close()
