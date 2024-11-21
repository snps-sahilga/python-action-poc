import os
import logging
import json
import requests
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
OPENAI_API_ENDPOINT = os.getenv("OPENAI_API_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

g = Github(auth = GITHUB_TOKEN)

# g = Github(base_url="https://{hostname}/api/v3", auth=auth) # Github Enterprise with custom hostname

class PRDetails:
    def __init__(self, owner, repo, pull_number, title, description):
        self.owner = owner
        self.repo = repo
        self.pull_number = pull_number
        self.title = title
        self.description = description

def get_pr_details():
    with open(os.getenv("GITHUB_EVENT_PATH"), "r") as f:
        event_data = json.load(f)
    repository = event_data["repository"]
    number = event_data["number"]
    pr = octokit.get_repo(f"{repository['owner']['login']}/{repository['name']}").get_pull(number)
    return PRDetails(
        owner=repository["owner"]["login"],
        repo=repository["name"],
        pull_number=number,
        title=pr.title or "",
        description=pr.body or ""
    )

def main():
    pr_details = get_pr_details()
    logging.info(pr_details)
    input_num = os.getenv('INPUT_NUM')
    try:
        number = int(input_num)
        square = number ** 2
        print(f"::set-output name=result::{square}")
    except ValueError:
        print("::error::Invalid input, please provide a number")

if __name__ == "__main__":
    main()