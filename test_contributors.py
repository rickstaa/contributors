"""This module contains the tests for the contributors.py module"""

import unittest
from unittest.mock import patch, MagicMock
from contributors import get_contributors, get_all_contributors


class TestContributors(unittest.TestCase):
    """
    Test case for the contributors module.
    """

    @patch("contributors.contributor_stats.ContributorStats")
    def test_get_contributors(self, mock_contributor_stats):
        """
        Test the get_contributors function.
        """
        mock_repo = MagicMock()
        mock_user = MagicMock()
        mock_user.login = "user"
        mock_user.avatar_url = "https://avatars.githubusercontent.com/u/12345678?v=4"
        mock_user.contributions_count = "100"
        mock_repo.contributors.return_value = [mock_user]
        mock_repo.full_name = "owner/repo"

        get_contributors(mock_repo, "2022-01-01", "2022-12-31")

        mock_contributor_stats.assert_called_once_with(
            "user",
            "https://avatars.githubusercontent.com/u/12345678?v=4",
            "100",
            "https://github.com/owner/repo/commits?author=user&since=2022-01-01&until=2022-12-31",
        )

    @patch("contributors.get_contributors")
    def test_get_all_contributors_with_organization(self, mock_get_contributors):
        """
        Test the get_all_contributors function when an organization is provided.
        """
        mock_github_connection = MagicMock()
        mock_github_connection.organization().repositories.return_value = [
            "repo1",
            "repo2",
        ]
        mock_get_contributors.return_value = [
            {"username": "user", "contribution_count": "100", "commits": "commit_url"}
        ]

        result = get_all_contributors(
            "org", "", "2022-01-01", "2022-12-31", mock_github_connection
        )

        self.assertEqual(
            result,
            [
                [
                    {
                        "username": "user",
                        "contribution_count": "100",
                        "commits": "commit_url",
                    }
                ]
            ]
            * 2,
        )
        mock_get_contributors.assert_any_call("repo1", "2022-01-01", "2022-12-31")
        mock_get_contributors.assert_any_call("repo2", "2022-01-01", "2022-12-31")

    @patch("contributors.get_contributors")
    def test_get_all_contributors_with_repository(self, mock_get_contributors):
        """
        Test the get_all_contributors function when a repository is provided.
        """
        mock_github_connection = MagicMock()
        mock_github_connection.repository.return_value = "repo"
        mock_get_contributors.return_value = [
            {"username": "user", "contribution_count": "100", "commits": "commit_url2"}
        ]

        result = get_all_contributors(
            "", "owner/repo", "2022-01-01", "2022-12-31", mock_github_connection
        )

        self.assertEqual(
            result,
            [
                [
                    {
                        "username": "user",
                        "contribution_count": "100",
                        "commits": "commit_url2",
                    }
                ]
            ],
        )
        mock_get_contributors.assert_called_once_with(
            "repo", "2022-01-01", "2022-12-31"
        )


if __name__ == "__main__":
    unittest.main()
