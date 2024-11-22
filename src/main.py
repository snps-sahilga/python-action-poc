import os
import json
import requests
import fnmatch
from github import Github
from unidiff import PatchSet

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
OPENAI_API_ENDPOINT = os.getenv("OPENAI_API_ENDPOINT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
EXCLUDE = os.getenv("exclude")

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
    print(pr.url)
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
    response = requests.get(pr.url, headers=headers)
    if response.status_code == 200:
        diff_content = response.text
        return diff_content
    else:
        print(f"Failed to get pull request diff: {response.status_code}")
        return

def create_prompt(file, pr_details):
    return f"""Your task is to review pull requests. Instructions:
    - Provide the response in following JSON format:  {"reviews": [{"lineNumber":  <line_number>, "reviewComment": <review comment>}]}
    - Do not give positive comments or compliments.
    - Provide comments and suggestions ONLY if there is something to improve, otherwise "reviews" should be an empty array.
    - Write the comment in GitHub Markdown format.
    - Use the given description only for the overall context and only comment the code.
    - IMPORTANT: NEVER suggest adding comments to the code.

    Review the following code diff in the file "{file.filename}" and take the pull request title and description into account when writing the response.

    Pull request title: {pr_details.title}
    Pull request description:

    ---
    {pr_details.description}
    ---

    Git diff to review:

    ```diff
    {file.patch}
    ```
    """

def analyze_code(parsed_diff, pr_details):
    comments = []
    for file in parsed_diff:
        if file.status == "removed":
            continue
        print(f"Filename: {file.filename}")
        print(f"Status: {file.status}")
        print(f"Additions: {file.additions}")
        print(f"Deletions: {file.deletions}")
        print(f"Changes: {file.changes}")
        print(f"SHA: {file.sha}")
        print(file.patch)
        print("************************************************")
#         patches = PatchSet(file.patch)
#         print(patches.path)
#         for hunk in patches.hunks:
#             print(section_header)
#             print(lines)
#         prompt = create_prompt(file, pr_details)
#         print(prompt)
#         ai_response = get_ai_response(prompt)
#         if ai_response:
#             new_comments = create_comment(file, chunk, ai_response)
#             if new_comments:
#                 comments.extend(new_comments)
#     return comments

def main():
    pr_details = get_pr_details()
    with open(os.getenv("GITHUB_EVENT_PATH"), "r") as f:
        event_data = json.load(f)
    if event_data["action"] == "opened":
#         diff = get_diff(pr_details.owner, pr_details.repo, pr_details.pull_number)
        pr = g.get_repo(f"{pr_details.owner}/{pr_details.repo}").get_pull(pr_details.pull_number)
        base = pr.base.sha
        head = pr.head.sha
        headers = {'Authorization': f"token {GITHUB_TOKEN}", 'Accept': 'application/vnd.github.v3.diff'}
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
        print(pr_url)
        response = requests.get(pr_url, headers=headers)
        print(diff)
#         pr = g.get_repo(f"{pr_details.owner}/{pr_details.repo}").get_pull(pr_details.pull_number)
        new_base_sha = pr.base.sha
        new_head_sha = pr.head.sha
#         print(pr.base)
#         print(pr.head)
    elif event_data["action"] == "synchronize":
        new_base_sha = event_data["before"]
        new_head_sha = event_data["after"]
        repo = g.get_repo(f"{pr_details.owner}/{pr_details.repo}")
        diff = repo.compare(new_base_sha, new_head_sha)
    else:
        print("Unsupported event:", os.getenv("GITHUB_EVENT_NAME"))
        return

    if diff == None:
        print("No Diff Found!!!")
        return

#     exclude_patterns = [s.strip() for s in EXCLUDE.split(",")]
#     filtered_diff = [file for file in diff.files if not any(fnmatch.fnmatch(file.filename, pattern) for pattern in exclude_patterns)]
#
#     analyze_code(filtered_diff, pr_details)

    input_num = os.getenv('INPUT_NUM')
    try:
        number = int(input_num)
        square = number ** 2
        print(f"::set-output name=result::{square}")
    except ValueError:
        print("::error::Invalid input, please provide a number")

if __name__ == "__main__":
    main()