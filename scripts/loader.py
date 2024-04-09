from neo4j import GraphDatabase
import json

class DataLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close the Neo4j database connection."""
        self.driver.close()

    def load_csv_data(self, csv_path, load_function):
        with self.driver.session() as session:
            session.execute_write(load_function, csv_path)

    @staticmethod
    def _load_authors(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (a:Author {{authorId: row.authorId}})
        ON CREATE SET a.name = row.name, a.affiliation = row.Affiliations,
        a.affiliationType = row.Affiliation_type
        """
        tx.run(query)

    @staticmethod

    def _load_authors_relations(tx, csv_filename):
        query_authors = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        UNWIND split(row.authorIds, ';') AS authorId
        MATCH (a:Author {{authorId: authorId}})
        MERGE (a)-[:WROTE]->(p)
        """
        tx.run(query_authors)

    @staticmethod
    def _load_corresponding_author_relations(tx, csv_filename):
        query_corresponding = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        MATCH (a:Author {{authorId: row.corresponding_author}})
        MERGE (a)-[:CORRESPONDING_AUTHOR]->(p)
        """
        tx.run(query_corresponding)

    @staticmethod
    def _load_venue_relations(tx, csv_filename, label):
        query_venue = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        MERGE (v:{label} {{name: row.venue}})
        ON CREATE SET v.year = toInteger(row.year), v.volume = row.journal_volume,
                    v.edition = row.edition
        MERGE (p)-[:PUBLISHED_IN]->(v)
        """
        tx.run(query_venue)

    @staticmethod
    def _load_citations(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        UNWIND apoc.convert.fromJsonList(row.citations) AS citation
        MATCH (cited:Paper {{paperId: citation}})
        MERGE (p)-[:CITES]->(cited)
        """
        tx.run(query)

        # Method to load conferences, journals, and workshops
    @staticmethod
    def _load_venues(tx, csv_filename, label):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (v:{label} {{name: row.name}})
        ON CREATE SET v.year = toInteger(row.year), v.volume = row.volume, 
                      v.edition = row.edition
        """
        tx.run(query)
    
    # Method to load keywords
    @staticmethod
    def _load_keywords(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        UNWIND split(row.keywords, ';') AS keyword
        MERGE (k:Keyword {{text: keyword}})
        """
        tx.run(query)

    # Method to create 'Reviewed' relationships
    @staticmethod
    def _load_reviews(tx, csv_filename):
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        UNWIND split(row.reviewers, ';') AS reviewerId
        MATCH (r:Author {{authorId: reviewerId}})
        MERGE (r)-[:REVIEWED]->(p)
        ON CREATE SET p.approved = row.approved, p.comments = row.comments
        """
        tx.run(query)
if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "propertygraph"
    loader = DataLoader(uri, user, password)

    # Corrected calls to include label for venue relations
    loader.load_csv_data("conference_info.csv", lambda tx, path: DataLoader._load_venue_relations(tx, path, 'Conference'))
    loader.load_csv_data("journal_info.csv", lambda tx, path: DataLoader._load_venue_relations(tx, path, 'Journal'))
    loader.load_csv_data("workshop_info.csv", lambda tx, path: DataLoader._load_venue_relations(tx, path, 'Workshop'))

    # Assuming that _load_authors_relations, _load_corresponding_author_relations, and _load_citation_relations
    # do not require additional arguments besides the csv_filename, those calls remain as is.
    loader.load_csv_data("authors_info.csv", DataLoader._load_authors)
    loader.load_csv_data("conference_info.csv", DataLoader._load_authors_relations)
    loader.load_csv_data("conference_info.csv", DataLoader._load_corresponding_author_relations)
    loader.load_csv_data("citations_info.csv", DataLoader._load_citations)

    loader.close()


    loader.close()