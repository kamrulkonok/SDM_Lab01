import configparser
import os

def load_config(config_file="config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file)

    uri = os.getenv("NEO4J_URI", config.get("neo4j", "uri"))
    user = os.getenv("NEO4J_USER", config.get("neo4j", "user"))
    password = os.getenv("NEO4J_PASSWORD", config.get("neo4j", "password"))
    database = os.getenv("NEO4J_DATABASE", config.get("neo4j", "database"))

    return {
        "uri": uri,
        "user": user,
        "password": password,
        "database": database
    }