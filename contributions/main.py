from os import getenv

import requests

USER = getenv("USER")


def main():
    # Get the PRs and prepare the contributions list
    prs = get_prs(USER)
    grouped_prs = group_prs(prs)
    sorted_prs = sort_prs(grouped_prs)
    contributions = create_contribution_list_md_format(sorted_prs)

    # Modify the README file
    find_beginning_and_end()
    modify_readme(contributions)


def get_prs(user):
    prs = requests.get(
        f"https://api.github.com/search/issues?q=author%3A{user}+type%3Apr",
    )

    prs_json: list = prs.json()["items"]
    filtered_prs = [pr for pr in prs_json if not pr["author_association"] == "OWNER"]

    return filtered_prs


def get_repo_description(repo):
    response = requests.get(
        f"https://api.github.com/repos/{repo}",
    )

    return response.json()["description"]


def group_prs(pull_requests):
    grouped_prs = {}

    for pr in pull_requests:
        repo = pr["repository_url"].replace("https://api.github.com/repos/", "")

        if repo not in grouped_prs:
            grouped_prs[repo] = {
                "url": f"https://github.com/{repo}/pulls?q=is%3Apr+author%3A{pr["user"]["login"]}",
                "description": get_repo_description(repo),
                "open": 0,
                "merged": 0,
            }

        if pr["state"] == "open":
            grouped_prs[repo]["open"] += 1
        elif pr["pull_request"]["merged_at"]:
            grouped_prs[repo]["merged"] += 1

    return grouped_prs


def sort_prs(grouped_prs):
    return dict(
        sorted(
            grouped_prs.items(),
            key=lambda x: x[1]["open"] + x[1]["merged"],
            reverse=True,
        )
    )


def create_contribution_list_md_format(grouped_prs):
    contributions = []

    for repo, pr in grouped_prs.items():
        pr_types = []
        if pr["merged"] > 0:
            pr_types.append(f'🟣 {pr["merged"]} merged')
        if pr["open"] > 0:
            pr_types.append(f"🟢 {pr['open']} open")

        pr_types_str = ", ".join(pr_types)
        repo_description = f' - *"{pr["description"]}"*' if pr["description"] else ""
        string = f'- [{repo}]({pr["url"]}) ({pr_types_str}){repo_description}'

        contributions.append(string)

    return contributions


def find_beginning_and_end():
    start_line = None
    end_line = None

    # Read file content
    with open("README.md", "r", encoding="utf8") as f:
        file_content = f.readlines()

    # Find the line that contains "github contributions"
    for index, line in enumerate(file_content):
        if "github contributions" in line.lower():
            start_line = index

        # After finding the line, get the first <br> tag after it
        if start_line and "<br>" in line:
            end_line = index

            return start_line, end_line
    else:
        exit("Can't find the beginning and end of the contributions section.")


def modify_readme(contribution_list):
    start_line, end_line = find_beginning_and_end()

    # Read file content
    with open("README.md", "r", encoding="utf8") as f:
        file_content = f.readlines()

    # Delete content between the start and end lines from the file content
    del file_content[start_line + 1 : end_line - 1]

    # Insert the new content at the start line
    file_content.insert(start_line + 1, "\n" + "\n".join(contribution_list) + "\n")

    # Write the modified content back to the file
    with open("README.md", "w", encoding="utf8") as f:
        f.writelines(file_content)


if __name__ == "__main__":
    main()
