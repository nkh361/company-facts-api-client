import unittest
import hashlib
import requests
from unittest.mock import patch
from client.api_client import get_challenge, solve_pow, fetch_data

class TestClient(unittest.TestCase):

    @patch('client.api_client.session.get')
    def test_get_challenge(self, mock_get):
        """ Test fetching the PoW challenge from the server. """

        # mock the server's response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "challenge_id": "abcd1234",
            "challenge": "datafeed12345",
            "difficulty": 4,
        }
        
        challenge_data = get_challenge("http://testapi")
        
        self.assertIn('challenge_id', challenge_data)
        self.assertIn('challenge', challenge_data)
        self.assertIn('difficulty', challenge_data)
        self.assertEqual(challenge_data['challenge_id'], "abcd1234")
        self.assertEqual(challenge_data['challenge'], "datafeed12345")
        self.assertEqual(challenge_data['difficulty'], 4)

    def test_solve_pow(self):
        """ Test solving the Proof of Work challenge. """

        challenge = "datafeed12345"
        difficulty = 4
        
        nonce = solve_pow(challenge, difficulty)
        
        # validate the result
        hash_value = hashlib.sha256(f"{challenge}{nonce}".encode()).hexdigest()
        self.assertTrue(
            hash_value.startswith("0" * difficulty),
            f"Hash {hash_value} does not meet difficulty {difficulty}"
        )

    @patch('client.api_client.session.post')
    def test_fetch_data(self, mock_post):
        """ Test fetching data from the server after solving PoW. """

        # mock the server's response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "data": {"price": 150.25, "volume": 123456}
        }
        
        # inputs
        challenge_id = "abcd1234"
        challenge = "datafeed12345"
        nonce = 67890
        difficulty = 4
        
        data = fetch_data("http://testapi", challenge_id, challenge, nonce, difficulty)
        
        self.assertIn('data', data)
        self.assertIn('price', data['data'])
        self.assertIn('volume', data['data'])
        self.assertEqual(data['data']['price'], 150.25)
        self.assertEqual(data['data']['volume'], 123456)

    @patch('client.api_client.session.post')
    def test_fetch_data_invalid_pow(self, mock_post):
        """ Test fetching data with an invalid PoW solution. """
        
        # mock the server's response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"error": "Invalid PoW solution"}
        mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error: Bad Request for url")

        challenge_id = "abcd1234"
        challenge = "datafeed12345"
        nonce = 1  # invalid 
        difficulty = 4
        
        with self.assertRaises(RuntimeError) as context:
            fetch_data("http://testapi", challenge_id, challenge, nonce, difficulty)
        
        self.assertIn("Failed to fetch data", str(context.exception))

if __name__ == '__main__':
    unittest.main()