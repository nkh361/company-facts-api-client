import requests
import hashlib
import sys
import json
import signal
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from rich import print

# configure retry logic for resilient HTTP requests
def get_session():
    session = requests.Session()
    retries = Retry(
        total=5,  # num of attempts
        backoff_factor=1,  # wait time multiplier between retries
        status_forcelist=[500, 502, 503, 504],  # retry on these status codes
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = get_session()

# handle graceful shutdown
def handle_signal(signum, frame):
    print("[bold red]Received shutdown signal. Exiting...[/]")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# fetch PoW challenge from the server
def get_challenge(api_url):
    try:
        response = session.get(f"{api_url}/challenge")
        response.raise_for_status()
        challenge_data = response.json()

        # validate response structure
        if not all(k in challenge_data for k in ("challenge_id", "challenge", "difficulty")):
            raise ValueError("Malformed response: missing keys")
        
        return challenge_data
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch challenge from {api_url}: {e}")

# solve Proof-of-Work challenge
def solve_pow(challenge, difficulty):
    nonce = 0
    prefix = "0" * difficulty
    while True:
        input_str = f"{challenge}{nonce}"
        hash_value = hashlib.sha256(input_str.encode()).hexdigest()
        if hash_value.startswith(prefix):
            return nonce
        nonce += 1

# submit PoW solution and fetch data from the server
def fetch_data(api_url, challenge_id, challenge, nonce, difficulty, entity_name):
    payload = {
        "challenge_id": challenge_id,
        "challenge": challenge,
        "nonce": nonce,
        "difficulty": difficulty,
        "entity_name": entity_name
    }
    try:
        response = session.post(f"{api_url}/data", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch data from {api_url}: {e}")

def main(api_url):
    try:
        # get pow challenge
        print("[italic white]Requesting challenge...[/]")
        challenge_data = get_challenge(api_url)
        challenge_id = challenge_data["challenge_id"]
        challenge = challenge_data["challenge"]
        difficulty = challenge_data["difficulty"]

        entity_name = "AAR CORP"
        
        print(f"[bold green]Received challenge[/]: [bold white]{challenge_id}, difficulty: {difficulty}[/]")

        # solve pow
        print("[italic white]Solving proof of work...[/]")
        nonce = solve_pow(challenge, difficulty)
        print(f"[bold green]Proof of work solved! Nonce[/]: [bold white]{nonce}[/]")

        # fetch data
        print("[italic white]Fetching data...[/]")
        data = fetch_data(api_url, challenge_id, challenge, nonce, difficulty, entity_name)

        # check if the data contains the facts key inside the nested dict
        # since the dict is nested, loop through each category (like dei) and subcategory (like EntityCommonStockSharesOutstanding) to check for the units key and count the units
        if isinstance(data, dict) and "data" in data and "facts" in data["data"]:
            facts = data["data"]["facts"]
            # TODO fix wrong number of matches returned
            num_matches = 0

            for category, category_data in facts.items():
                for subcategory, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, dict) and "units" in subcategory_data:
                        num_matches += len(subcategory_data["units"])
        else:
            num_matches = 0

        print(f"[bold green]Entity name identified! Number of matches: {num_matches}")
        json_string_data = json.dumps(data, indent=6)
        print(f"[bold green]Received data[/]: [bold white]{json.loads(json_string_data)}[/]")
        
    except RuntimeError as e:
        print(f"[bold red]Error: {e}[/]")

if __name__ == "__main__":
    # dynamic API URL via CLI argument or default to localhost
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
    main(api_url)