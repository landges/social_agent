import numpy as np
import requests
import sys
import json
import datetime
from api_keys import GIT_AUTH_NAME, GIT_TOKEN


def score_user(username: str):
    '''

    :param username:
    :return: score for username

    score calculated the following formula:
    sqrt(num_followers)+sqrt(num_public_gists)+sqrt(
    num_stars)+num_languages+activity_user+repos_num+commit_score+repo_num_branches + repo_num_issues
    '''
    # (2 * commits in repo + comments in repo) for each repo
    user_data = json.loads(requests.get(f'https://api.github.com/users/{username}', auth=(GIT_AUTH_NAME, GIT_TOKEN)).text)
    num_followers = np.sqrt(user_data['followers'])
    num_public_gists = np.sqrt(user_data['public_gists'])
    languages = {}  # contains all the languages used and the frequency of their use
    page_no = 1
    user_repos = []
    repos_url = user_data['repos_url']
    while True:
        response = requests.get(repos_url, auth=(GIT_AUTH_NAME, GIT_TOKEN))
        response = response.json()
        user_repos = user_repos + response
        repos_fetched = len(response)
        if repos_fetched == 30:  # API get only 30 repo for one request
            page_no = page_no + 1
            repos_url = user_data['repos_url'] + '?page=' + str(page_no)
        else:
            break
    repos_num = np.sum([0.5 if repo['fork'] else 1 for repo in user_repos])
    print(f'Total num of repos for {username}: {len(user_repos)}\n')
    num_stars = 0
    updates_dates_delta = []
    now_date = datetime.datetime.now()
    total_score = repos_num
    for repo in user_repos:
        language_response = json.loads(requests.get(repo['languages_url'], auth=(GIT_AUTH_NAME, GIT_TOKEN)).text)
        num_stars += repo['stargazers_count']
        updates_dates_delta.append((now_date - datetime.datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')).days)
        for key, value in language_response.items():
            languages[key] = languages.get(key, 0) + value
        repo_num_branches = len(
            json.loads(requests.get(repo['branches_url'].split('{')[0], auth=(GIT_AUTH_NAME, GIT_TOKEN)).text))
        repo_num_issues = len(
            json.loads(requests.get(repo['issues_url'].split('{')[0], auth=(GIT_AUTH_NAME, GIT_TOKEN)).text))

        url = repo['commits_url'].split('{')[0]
        page_no = 1
        repo_commits = []
        while True:
            response = requests.get(url, auth=(GIT_AUTH_NAME, GIT_TOKEN))
            response = response.json()
            if isinstance(response, list):
                repo_commits = repo_commits + response
            if len(response) == 30:
                page_no = page_no + 1
                url = repo['commits_url'].split('{')[0] + '?page=' + str(page_no)
            else:
                break

        if isinstance(repo_commits, list):
            repo_commits_score = np.sum(
                [1 / (1 + 5 * np.exp(-len(commit['commit']['message'].split()))) for commit in repo_commits])
        else:
            repo_commits_score = 0

        print(
            f'For repo {repo["name"]} scores are:\nbranches score {repo_num_branches}, basic issues score {repo_num_issues}, commits score {np.round(np.sqrt(repo_commits_score), 2)}')
        total_score += repo_num_branches + repo_num_issues + np.sqrt(repo_commits_score)

    print(f'For user {username} frequency languages: ' + str(languages.keys()))
    num_languages = len(languages.items())
    date_score = np.sum([1 if delta < 365 else -0.3 for delta in updates_dates_delta])
    total_score = total_score + num_languages + num_followers + num_public_gists + np.sqrt(num_stars) + date_score
    return total_score


if __name__ == '__main__':
    print('\n')
    print(f'\nThe final {sys.argv[1]} score is {np.round(score_user(sys.argv[1]), 2)}')
    # big user for test: benawad
    # print(score_user('benawad'))
    # username = 'xtonev'

