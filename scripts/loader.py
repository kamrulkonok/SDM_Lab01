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
        query = """
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (a:Author {{authorId: row.authorId}})
        ON CREATE SET a.name = row.name, a.affiliation = row.Affiliations,
        a.affiliationType = row.Affiliation_type
        """
        tx.run(query.format(csv_filename=csv_filename))

    @staticmethod
    def _load_papers_and_relationships(tx, csv_filename, label):
        # Creates Paper nodes
        query_paper = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (p:Paper {{paperId: row.paperId}})
        ON CREATE SET p.title = row.title, p.url = row.url, p.abstract = row.abstract,
                    p.year = toInteger(row.year), p.citationCount = toInteger(row.citationCount),
                    p.keywords = row.keywords
        """
        tx.run(query_paper)

        # Load relationships to authors
        query_authors = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        UNWIND split(row.authorIds, ';') AS authorId
        MATCH (a:Author {{authorId: authorId}})
        MERGE (a)-[:WROTE]->(p)
        """
        tx.run(query_authors)

        # Set corresponding authors
        query_corresponding = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {{paperId: row.paperId}})
        MATCH (a:Author {{authorId: row.corresponding_author}})
        MERGE (a)-[:CORRESPONDING_AUTHOR]->(p)
        """
        tx.run(query_corresponding)

        # Link to venues (conference, journal, workshop)
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
        query = """
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {paperId: row.paperId})
        UNWIND json.loads(row.citations) AS citation
        MATCH (cited:Paper {paperId: citation})
        MERGE (p)-[:CITES]->(cited)
        """
        tx.run(query.format(csv_filename=csv_filename))

        # Method to load conferences, journals, and workshops
    @staticmethod
    def _load_venues(tx, csv_filename, label):
        query = """
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MERGE (v:{label} {name: row.name})
        ON CREATE SET v.year = toInteger(row.year), v.volume = row.volume, 
                      v.edition = row.edition
        """
        tx.run(query.format(csv_filename=csv_filename, label=label))
    
    # Method to load keywords
    @staticmethod
    def _load_keywords(tx, csv_filename):
        query = """
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        UNWIND split(row.keywords, ';') AS keyword
        MERGE (k:Keyword {text: keyword})
        """
        tx.run(query.format(csv_filename=csv_filename))

    # Method to create 'Reviewed' relationships
    @staticmethod
    def _load_reviews(tx, csv_filename):
        query = """
        LOAD CSV WITH HEADERS FROM 'file:///{csv_filename}' AS row
        MATCH (p:Paper {paperId: row.paperId})
        UNWIND split(row.reviewers, ';') AS reviewerId
        MATCH (r:Author {authorId: reviewerId})
        MERGE (r)-[:REVIEWED]->(p)
        ON CREATE SET p.approved = row.approved, p.comments = row.comments
        """
        tx.run(query.format(csv_filename=csv_filename))

if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "propertygraph"
    loader = DataLoader(uri, user, password)

    loader.load_csv_data("authors_info.csv", DataLoader._load_authors)
    loader.load_csv_data("conference_info.csv", lambda tx, path: DataLoader._load_papers_and_relationships(tx, path, 'ConferencePaper'))
    loader.load_csv_data("journal_info.csv", lambda tx, path: DataLoader._load_papers_and_relationships(tx, path, 'JournalPaper'))
    loader.load_csv_data("workshop_info.csv", lambda tx, path: DataLoader._load_papers_and_relationships(tx, path, 'WorkshopPaper'))
    loader.load_csv_data("citations_info.csv", DataLoader._load_citations)

    loader.close()