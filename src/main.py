import os
import json
import requests
from github import Github

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
OPENAI_API_ENDPOINT = os.getenv("OPENAI_API_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")

g = Github(GITHUB_TOKEN)

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
    pr = g.get_repo(f"{repository['owner']['login']}/{repository['name']}").get_pull(number)
    return PRDetails(
        owner=repository["owner"]["login"],
        repo=repository["name"],
        pull_number=number,
        title=pr.title or "",
        description=pr.body or ""
    )

def get_diff(owner, repo, pull_number):
    pr = g.get_repo(f"{owner}/{repo}").get_pull(pull_number)
    headers = {'Authorization': f"token {GITHUB_TOKEN}", 'Accept': 'application/vnd.github.v3.diff'}
    response = requests.get(pr.url, headers=headers)
    if response.status_code == 200:
        diff_content = response.text
        return diff_content
    else:
        print(f"Failed to get pull request diff: {response.status_code}")
        return

def main():
    pr_details = get_pr_details()
    with open(os.getenv("GITHUB_EVENT_PATH"), "r") as f:
        event_data = json.load(f)
    if event_data["action"] == "opened":
#         diff = get_diff(pr_details.owner, pr_details.repo, pr_details.pull_number)
        print("Opened")
        new_base_sha = pr_details.base.sha
        new_head_sha = pr_details.head.sha
        repo = g.get_repo(f"{pr_details.owner}/{pr_details.repo}")
        diff = repo.compare(new_base_sha, new_head_sha)
    elif event_data["action"] == "synchronize":
        print("Synchronized")
        new_base_sha = event_data["before"]
        new_head_sha = event_data["after"]
        repo = g.get_repo(f"{pr_details.owner}/{pr_details.repo}")
        diff = repo.compare(new_base_sha, new_head_sha)
    if diff == None:
        print("No Diff Found!!!")
        return
    else:
#         print(diff)
        print(f"Status of comparison: {diff.status}")
        print(f"Total commits in the comparison: {diff.total_commits}")

        # Iterate over the files in the comparison
        for file in diff.files:
            print(f"Filename: {file.filename}")
            print(f"Status: {file.status}")
            print(f"Additions: {file.additions}")
            print(f"Deletions: {file.deletions}")
            print(f"Changes: {file.changes}")
            print(file.patch)
            print("")
    input_num = os.getenv('INPUT_NUM')
    try:
        number = int(input_num)
        square = number ** 2
        print(f"::set-output name=result::{square}")
    except ValueError:
        print("::error::Invalid input, please provide a number")

if __name__ == "__main__":
    main()