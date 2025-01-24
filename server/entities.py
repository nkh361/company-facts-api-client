from datetime import datetime
from rich import print
import json

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

class EntityFactory:

    @staticmethod
    def create_response(status: str, message: str, data: dict = None) -> dict:
        """ Create a standardized response object. """
        return {
            "status": status,
            "message": message,
            "data": data or {}
        }
    
    @staticmethod
    def create_company_facts(company_name: str, facts: dict) -> dict:
        """ Create a method object for company facts. """
        return {
            "company_name": company_name,
            "facts": facts,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_response_with_company_facts(status: str, message: str, company_name: str, facts: dict) -> dict:
        company_facts = EntityFactory.create_company_facts(company_name, facts)
        return EntityFactory.create_response(status, message, data=company_facts)

##############################################################
#                       Example uses                         #
##############################################################

# response = EntityFactory.create_response(
#     status="success",
#     message="request processed successfully",
#     data = {"key": "value"}
# )

# company_facts = EntityFactory.create_company_facts(
#     company_name="apple",
#     facts = {"revenue": "1B", "employees": 69}
# )

# best_response = EntityFactory.create_response_with_company_facts(
#     status = "success",
#     message = "company facts retrieved successfully.",
#     company_name = "acme group",
#     facts = {"revenue": "1B", "employees": 1000}
# )

# print(f"[bold magenta]Response: \n[/]{json.dumps(response, indent=4)}\n")
# print(f"[bold magenta]Company Facts: \n[/]{json.dumps(company_facts, indent=4)}\n")
# print(f"[bold magenta]Best response: \n[/]{json.dumps(best_response, indent=4)}\n")

# file_path = "../datasource/CIK0000001750.json"

# with open(file_path, 'r') as f:
#     try:
#         data = json.load(f)
#         test_run = EntityFactory.create_response_with_company_facts(
#             status="success",
#             message="company facts retrieved successfully.",
#             company_name=data["entityName"],
#             facts=data["facts"]
#         )
#         print(f"[bold magenta]Trial return: \n[/]{json.dumps(test_run, indent=4)}")
#     except json.JSONDecodeError as e:
#         print("Invalid JSON:", e)