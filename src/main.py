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
    print(pr.url)
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.diff'}
#     headers = {'Accept': 'application/vnd.github.v3.diff'}
#     response = g._Github__requester.requestRaw("GET", pr.url, headers=headers)
#     print(response.text)
#     print(response.status_code)
#
    response = requests.get(pr.diff_url, headers=headers)
    if response.status_code == 200:
        diff_content = response.text
        print("Pull request diff:")
        print(diff_content)
        return diff_content
    else:
        print(f"Failed to get pull request diff: {response.status_code}")
        print(response.text)
        return
#     pr_diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    # Fetch the pull request diff
#     try:
#         pr_response = requests.get(pr_diff_url, headers=headers)
#
#         if pr_response.status_code == 200:
#             pr_data = pr_response.json()
#             diff_url = pr_data.get('diff_url')
#
#             if diff_url:
#                 diff_response = requests.get(diff_url, headers=headers)
#                 if diff_response.status_code == 200:
#                     diff_content = diff_response.text
#                     print("Pull request diff:")
#                     print(diff_content)
#                 else:
#                     print(f"Failed to get pull request diff: {diff_response.status_code}")
#                     print(diff_response.text)
#             else:
#                 print("No diff URL found in pull request data.")
#         else:
#             print(f"Failed to get pull request: {pr_response.status_code}")
#             print(pr_response.text)
#             return
#     except Exception as e:
#         print(f"Exception occurred while fetching pull request data: {e}")
#         return

def main():
    pr_details = get_pr_details()
    with open(os.getenv("GITHUB_EVENT_PATH"), "r") as f:
        event_data = json.load(f)
    if event_data["action"] == "opened":
        diff = get_diff(pr_details.owner, pr_details.repo, pr_details.pull_number)
    print(diff)
    input_num = os.getenv('INPUT_NUM')
    try:
        number = int(input_num)
        square = number ** 2
        print(f"::set-output name=result::{square}")
    except ValueError:
        print("::error::Invalid input, please provide a number")

if __name__ == "__main__":
    main()