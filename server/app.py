from flask import Flask, request, jsonify
import hashlib
import time
import logging
import os
import json
import csv
from entities import EntityFactory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from rich import print
from rich.logging import RichHandler

# initialize server
app = Flask(__name__)

# configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = RichHandler(rich_tracebacks=True)
logger.addHandler(handler)

# redis for caching challenges
try:
    redis_client = Redis(host="localhost", port=6379, db=0)
    redis_client.ping()
    print("[bold green]Redis connection successful.[/]")
except Exception as e:
    print(f"[bold red]Failed to connect to redis: {e}[/]")

# flask-limiter for rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])

# constants
CHALLENGE_EXPIRATION = 60; # in seconds
DATASOURCE_DIR = "../datasource"

# sanity check
@app.route('/sanity', methods=['GET'])
def sanity_check():
    return jsonify({"status": "healthy"}), 200

# generate challenge
@app.route('/challenge', methods=['GET'])
@limiter.limit("10 per minute")
def get_challenge():
    """ Generates a unique challenge with an expiration time. """

    challenge = "datafeed" + str(int(time.time()))
    challenge_id = hashlib.sha256(challenge.encode()).hexdigest()
    difficulty = 4

    # store challenge in redis with an expiration
    redis_client.setex(challenge_id, CHALLENGE_EXPIRATION, challenge)
    logger.info(f"Generated challenge: {challenge_id}, difficulty: {difficulty}")
    return jsonify({"challenge_id": challenge_id, "challenge": challenge, "difficulty": difficulty})

# verify pow and provide data
@app.route('/data', methods=['POST'])
def verify_pow():
    """ Validates the proof of work solution and returns data. """

    data = request.json
    challenge_id = data.get("challenge_id")
    challenge = data.get("challenge")
    nonce = data.get("nonce")
    difficulty = data.get("difficulty")
    entity_name = data.get("entity_name")

    # validate inputs
    if not all([challenge_id, challenge, isinstance(nonce, int), isinstance(difficulty, int)]):
        logger.warning("Invalid request format.")
        return jsonify({"error": "Invalid request format."}), 400
    
    # check if the challenge is valid AND not expired
    stored_challenge = redis_client.get(challenge_id)
    if not stored_challenge or stored_challenge.decode() != challenge:
        logger.warning("Challenge expired or invalid.")
        return jsonify({"error": "Challenge expired or invalid"}), 400
    
    # verify proof of work
    hash_value = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
    if hash_value.startswith("0" * difficulty):
        logger.info(f"Valid PoW solution received for challenge: {challenge_id}")

        try:
            files = os.listdir(DATASOURCE_DIR)
            if not files:
                return jsonify(EntityFactory.create_response("Error", "Invalid request format.")), 400
            
            # list of entityName file matches
            matches = []

            for file_name in files:
                file_path = os.path.join(DATASOURCE_DIR, file_name)
                try:
                    with open(file_path, 'r') as infile:
                        if file_path.endswith('.json'):
                            file_data = json.load(infile)
                            if file_data.get("entityName") == entity_name:
                                matches.append(EntityFactory.create_company_facts(
                                    company_name=file_data.get("entityName"),
                                    facts=file_data.get("facts", {})
                                ))
                        elif file_path.endswith('.csv'):
                            reader = csv.DictReader(infile)
                            for row in reader:
                                if row.get("entityName") == entity_name:
                                    matches.append(EntityFactory.create_company_facts(
                                        company_name=row.get("entityName"),
                                        facts=row
                                    ))
                        else:
                            logger.warning(f"Unsupported file format: {file_name}")
                except Exception as e:
                    logger.error(f"Error reading file {file_name}: {e}")

            if matches:
                return jsonify(EntityFactory.create_response(
                    "success",
                    "Entity matches retrieved",
                    data={"matches": matches}
                ))
            else:
                return jsonify(EntityFactory.create_response(
                    "not_found",
                    "No matching entities found."
                )), 404
            
        except Exception as e:
            logger.error(f"Failed to read datasource: {e}")
            return jsonify(EntityFactory.create_response("error", "Failed to fetch data.")), 500
    
    else:
        logger.warning("Invalid PoW solution.")
        return jsonify(EntityFactory.create_response("error", "Invalid PoW solution.")), 400
    
if __name__ == "__main__":
    app.run(debug=True)