# pylint: disable=broad-exception-caught
"""This file contains the main() and other functions needed to get contributor information from the organization or repository"""

from typing import List

import auth
import contributor_stats
import env
import json_writer
import markdown


def main():
    """Run the main program"""

    # Get environment variables
    (
        organization,
        repository_list,
        gh_app_id,
        gh_app_installation_id,
        gh_app_private_key,
        gh_app_enterprise_only,
        token,
        ghe,
        start_date,
        end_date,
        sponsor_info,
        link_to_profile,
        include_forks,
    ) = env.get_env_vars()

    # Auth to GitHub.com
    github_connection = auth.auth_to_github(
        token,
        gh_app_id,
        gh_app_installation_id,
        gh_app_private_key,
        ghe,
        gh_app_enterprise_only,
    )

    if not token and gh_app_id and gh_app_installation_id and gh_app_private_key:
        token = auth.get_github_app_installation_token(
            ghe, gh_app_id, gh_app_private_key, gh_app_installation_id
        )

    # Get the contributors
    contributors = get_all_contributors(
        organization,
        repository_list,
        start_date,
        end_date,
        github_connection,
        include_forks,
        ghe,
    )

    # Check for new contributor if user provided start_date and end_date
    if start_date and end_date:
        # get the list of contributors from before start_date
        # so we can see if contributors after start_date are new or returning
        returning_contributors = get_all_contributors(
            organization,
            repository_list,
            start_date="2008-02-29",  # GitHub was founded on 2008-02-29
            end_date=start_date,
            github_connection=github_connection,
            forks=include_forks,
            ghe=ghe,
        )
        for contributor in contributors:
            contributor.new_contributor = contributor_stats.is_new_contributor(
                contributor.username, returning_contributors
            )

    # Get sponsor information on the contributor
    if sponsor_info == "true":
        contributors = contributor_stats.get_sponsor_information(
            contributors, token, ghe
        )
    # Output the contributors information
    # print(contributors)
    markdown.write_to_markdown(
        contributors,
        "contributors.md",
        start_date,
        end_date,
        organization,
        repository_list,
        sponsor_info,
        link_to_profile,
        ghe,
    )
    json_writer.write_to_json(
        filename="contributors.json",
        start_date=start_date,
        end_date=end_date,
        organization=organization,
        repository_list=repository_list,
        sponsor_info=sponsor_info,
        link_to_profile=link_to_profile,
        contributors=contributors,
    )


def get_all_contributors(
    organization: str,
    repository_list: List[str],
    start_date: str,
    end_date: str,
    github_connection: object,
    include_forks: bool,
    ghe: str,
):
    """
    Get all contributors from the organization or repository

    Args:
        organization (str): The organization for which the contributors are being listed.
        repository_list (List[str]): The repository list for which the contributors are being listed.
        start_date (str): The start date of the date range for the contributor list.
        end_date (str): The end date of the date range for the contributor list.
        include_forks (bool): Whether to include contributor information from forks.
        github_connection (object): The authenticated GitHub connection object from PyGithub

    Returns:
        all_contributors (list): A list of ContributorStats objects
    """
    repos = []
    if organization:
        repos = github_connection.organization(organization).repositories()
    else:
        repos = []
        for repo in repository_list:
            owner, repo_name = repo.split("/")
            repository_obj = github_connection.repository(owner, repo_name)
            repos.append(repository_obj)

    all_contributors = []
    if repos:
        for repo in repos:
            if include_forks or not repo.fork:
                repo_contributors = get_contributors(repo, start_date, end_date, ghe)
                if repo_contributors:
                    all_contributors.append(repo_contributors)

    # Check for duplicates and merge when usernames are equal
    all_contributors = contributor_stats.merge_contributors(all_contributors)

    return all_contributors


def get_contributors(repo: object, start_date: str, end_date: str, ghe: str):
    """
    Get contributors from a single repository and filter by start end dates if present.

    Args:
        repo (object): The repository object from PyGithub
        start_date (str): The start date of the date range for the contributor list.
        end_date (str): The end date of the date range for the contributor list.

    Returns:
        contributors (list): A list of ContributorStats objects
    """
    all_repo_contributors = repo.contributors()
    contributors = []
    try:
        for user in all_repo_contributors:
            # Ignore contributors with [bot] in their name
            if "[bot]" in user.login:
                continue

            # Check if user has commits in the date range
            if start_date and end_date:
                user_commits = repo.commits(
                    author=user.login, since=start_date, until=end_date
                )

                # If the user has no commits in the date range, skip them
                try:
                    next(user_commits)
                except StopIteration:
                    continue

            # Store the contributor information in a ContributorStats object
            endpoint = ghe if ghe else "https://github.com"
            if start_date and end_date:
                commit_url = f"{endpoint}/{repo.full_name}/commits?author={user.login}&since={start_date}&until={end_date}"
            else:
                commit_url = f"{endpoint}/{repo.full_name}/commits?author={user.login}"
            contributor = contributor_stats.ContributorStats(
                user.login,
                False,
                user.avatar_url,
                user.contributions_count,
                commit_url,
                "",
            )
            contributors.append(contributor)
    except Exception as e:
        print(f"Error getting contributors for repository: {repo.full_name}")
        print(e)
        return None

    return contributors


if __name__ == "__main__":
    main()
