import unittest
import hashlib
import json
from server.app import app, redis_client

class TestServer(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        # clear redis after each test
        redis_client.flushdb()

    def test_challenge_endpoint(self):
        """ Test if the challenge endpoint returns a valid challenge. """

        response = self.app.get('/challenge')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn("challenge_id", data)
        self.assertIn("challenge", data)
        self.assertIn("difficulty", data)
        self.assertIsInstance(data["difficulty"], int)

        # validate redis storage of the challenge
        stored_challenge = redis_client.get(data["challenge_id"])
        self.assertIsNotNone(stored_challenge)
        self.assertEqual(stored_challenge.decode(), data["challenge"])

    def find_nonce(self, challenge, difficulty):
        """ Helper function to find a valid nonce. """

        nonce = 0
        prefix = "0" * difficulty
        while True:
            hash_value = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
            if hash_value.startswith(prefix):
                return nonce
            nonce += 1

    def test_data_endpoint_valid_pow(self):
        """ Test if the data endpoint accepts a valid PoW solution. """

        # generate a challenge
        challenge_response = self.app.get('/challenge')
        self.assertEqual(challenge_response.status_code, 200)
        challenge_data = json.loads(challenge_response.data)

        challenge_id = challenge_data["challenge_id"]
        challenge = challenge_data["challenge"]
        difficulty = challenge_data["difficulty"]

        # solve the PoW
        nonce = self.find_nonce(challenge, difficulty)

        payload = {
            "challenge_id": challenge_id,
            "challenge": challenge,
            "nonce": nonce,
            "difficulty": difficulty,
        }
        
        response = self.app.post('/data', json=payload)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('data', data)
        self.assertIn('price', data['data'])
        self.assertIn('volume', data['data'])

    def test_data_endpoint_invalid_pow(self):
        """ Test if the data endpoint rejects an invalid PoW solution. """
        # generate a challenge
        challenge_response = self.app.get('/challenge')
        self.assertEqual(challenge_response.status_code, 200)
        challenge_data = json.loads(challenge_response.data)

        challenge_id = challenge_data["challenge_id"]
        challenge = challenge_data["challenge"]
        difficulty = challenge_data["difficulty"]

        # use an invalid nonce
        invalid_nonce = 1

        payload = {
            "challenge_id": challenge_id,
            "challenge": challenge,
            "nonce": invalid_nonce,
            "difficulty": difficulty,
        }
        
        response = self.app.post('/data', json=payload)
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_data_endpoint_expired_challenge(self):
        """ Test if the data endpoint rejects an expired challenge. """
        
        # generate a challenge
        challenge_response = self.app.get('/challenge')
        self.assertEqual(challenge_response.status_code, 200)
        challenge_data = json.loads(challenge_response.data)

        challenge_id = challenge_data["challenge_id"]
        challenge = challenge_data["challenge"]
        difficulty = challenge_data["difficulty"]

        # simulate expiration by manually deleting the challenge from redis
        redis_client.delete(challenge_id)

        # solve the PoW
        nonce = self.find_nonce(challenge, difficulty)

        payload = {
            "challenge_id": challenge_id,
            "challenge": challenge,
            "nonce": nonce,
            "difficulty": difficulty,
        }

        response = self.app.post('/data', json=payload)
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Challenge expired or invalid")


if __name__ == '__main__':
    unittest.main()