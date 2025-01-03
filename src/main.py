import os
import json
import requests
import fnmatch
from github import Github
from unidiff import PatchSet
from openai import AzureOpenAI

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

def create_prompt(hunk, filename, pr_details):
    return f"""Your task is to review pull requests. Instructions:
    - Provide the response in following JSON format:  {{"reviews": [{{"lineNumber":  <line_number>, "reviewComment": <review comment>}}]}}
    - Do not give positive comments or compliments.
    - Provide comments and suggestions ONLY if there is something to improve, otherwise "reviews" should be an empty array.
    - Write the comment in GitHub Markdown format.
    - Use the given description only for the overall context and only comment the code.
    - IMPORTANT: NEVER suggest adding comments to the code.

    Review the following code diff in the file "{filename}" and take the pull request title and description into account when writing the response.

    Pull request title: {pr_details.title}
    Pull request description:

    ---
    {pr_details.description}
    ---

    Git diff to review:

    ```diff
    {hunk}
    ```
    """

def get_ai_response(prompt):
    client = AzureOpenAI(azure_endpoint = OPENAI_API_ENDPOINT, api_key = OPENAI_API_KEY, api_version = OPENAI_API_VERSION)
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(model = OPENAI_API_MODEL, messages=messages)
    print(response.choices[0].message.content)
    client.close()
#     return json.loads(response_json["choices"][0]["text"].strip()).get("reviews", [])

def analyze_code(diff, pr_details):
    patches = PatchSet(diff)
    exclude_patterns = [s.strip() for s in EXCLUDE.split(",")]
    comments = []
    for patch in patches:
        if patch.is_removed_file or any(fnmatch.fnmatch(patch.path, pattern) for pattern in exclude_patterns):
            continue
        for hunk in patch:
            prompt = create_prompt(hunk, patch.path, pr_details)
            get_ai_response(prompt)
            print("---------------------------------")
        print("************************************************")

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
        pr = g.get_repo(f"{pr_details.owner}/{pr_details.repo}").get_pull(pr_details.pull_number)
        base = pr.base.sha
        head = pr.head.sha
    elif event_data["action"] == "synchronize":
        base = event_data["before"]
        head = event_data["after"]
    else:
        print("Unsupported event:", os.getenv("GITHUB_EVENT_NAME"))
        return

    headers = {'Authorization': f"token {GITHUB_TOKEN}", 'Accept': 'application/vnd.github.v3.diff'}
    pr_url = f"https://api.github.com/repos/{pr_details.owner}/{pr_details.repo}/compare/{base}...{head}"
    response = requests.get(pr_url, headers=headers)

    if response.status_code == 200:
        diff = response.text
    else:
        print(f"Failed to get pull request diff: {response.status_code}")
        return

    if diff == None:
        print("No Diff Found!!!")
        return

    analyze_code(diff, pr_details)

    input_num = os.getenv('INPUT_NUM')
    try:
        number = int(input_num)
        square = number ** 2
        print(f"::set-output name=result::{square}")
    except ValueError:
        print("::error::Invalid input, please provide a number")

if __name__ == "__main__":
    main()