#!/usr/bin/env python
"""
Acronyms:
- mcs : mission critical settings

pull reequest number can be

Make sure to comment on all such commits where the changes to the respective files were made

Comment on PR page must contain the following details:
- Who created the PR
- Where in the file changes were made
"""
import subprocess
import sys
import json
import traceback
import requests
from flask import Response
from flask import Flask
from flask import request

# ------------------------------------imports from module--------------------------

import create_comment_on_PR as createComment
import send_status_on_PR as sendStatus
import mcs_config

RETURN_MSG = "Meliora cogito #DBL"
DIR_ITEM_SET = set(mcs_config.DIRS)

app = Flask(__name__)
def get_author(commit):
    """
    """
    return commit["commit"]["author"]["name"]

def get_committer(commit):
    """
        gets username of committer

        :param commit: commit dict
        :return: username of committer
        """
    return commit["commit"]["committer"]["name"]


def get_head_branch(payload):
    """
        gets the branch where the head is

        :param payload: payload from webhook
        :return: return the branch
        """
    return payload["pull_request"]["head"]["ref"]


def get_repo_owner(payload):
    """
        gets the repo owner

        :param payload: payload from webhook
        :return: return tuple of login and name of repo owner
        """
    r = requests.get(payload["repository"]["owner"]["url"])
    return (r.json()["login"], r.json()["name"])


def get_repo_name(payload):
    """
        gets the repo name

        :param payload: payload from webhook
        :return: repo owner
        """
    return payload["repository"]["name"]


def get_PR_number(payload):
    """
        get the PR number. The pull request number is one of the keys payload dictionary itself

        :param payload: payload from the webhook
        :return: repo owner
        """
    return payload["number"]


def get_commits(payload):
    """
        gets all commits for a particular pull request

        :param payload: payload from the webhook
        :return:list of all commits for that particular PR
        """
    r = requests.get(payload["pull_request"]["commits_url"])
    # r.json() will be a list of all commits
    commits = r.json()
    return commits


def get_commit_id(commit):
    """
        Gets the commit ids of the PR

        :param payload: payload from the webhook
        :return: commit hash list
        """
    return commit["sha"]


def get_files_changed(commit):
    """
    Gets the files changed for a commit

    :param commit: commit
    :return: list of files changed
    """
    r = requests.get(commit["url"])
    files_changed = r.json()["files"]
    return files_changed


def get_file_path(file):
    """
        gets the file path for a given file

        :param file: dictionary of file details
        :return: file path
        """
    return file["filename"]


def get_position_to_comment(file):
    """
    gets line number to comment. Note that here we are only interested in getting the post image
    line number of the git diff.

    :param payload: payload from the webhook
    :return: line number
        """
    patch = file["patch"]
    patch = patch.split('@@')
    patch = patch[1].split(' ')
    preimage = patch[1]
    postimage = patch[2]
    preimage_start_line = preimage.split(',')[0]
    postimage_start_line = postimage.split(',')[0]
    # for now we are only interested in returning the postimage line number, thats all
    return int(postimage_start_line)


def get_head_sha_hash(payload):
    """
        gets the head sha hash

        :param payload: payload from webhook
        :return: line number
        """
    return payload["pull_request"]["head"]["sha"]


@app.route('/', methods=['POST'])
def get_github_webhook_request():
    resp = Response()
    if request.is_json:
        print "request is json"
        parsed_json = request.json
        print "json parsed"
        try:
            # the change is mission critical
            repo_name = get_repo_name(parsed_json)
            print repo_name
            if repo_name not in mcs_config.REPO_NAMES:
                return RETURN_MSG
            pr_head_branch = get_head_branch(parsed_json)
            print pr_head_branch
            if pr_head_branch not in mcs_config.BRANCHES:
                return RETURN_MSG

            head_sha_hash = get_head_sha_hash(parsed_json)
            repo_login, repo_owner = get_repo_owner(parsed_json)
            pr_number = get_PR_number(parsed_json)

            print "head_sha_hash now: " + head_sha_hash

            # print head_sha_hash + "," + repo_login + "," + repo_owner + "," + pr_number
            # now there will be a check on the commits in and if in any commit a file
            # change is found that is in the list of possible file changes then comment on
            # those changes

            MCS_FILE_EDITED = False

            commits = get_commits(parsed_json)
            for commit in commits:
                # print "current_commit: "+commit
                committer = get_committer(commit)
                author = get_author(commit)
                commit_id = get_commit_id(commit)
                print "commit_id:" + commit_id
                files = get_files_changed(commit)
                for file in files:
                    
                    if MCS_FILE_EDITED == True:
                        print "MCS true"
                        sendStatus.send(-1, repo_login, repo_name,
                                        head_sha_hash, "pending")
                    filepath = get_file_path(file)

                    dir_items = set(filepath.split('/'))
                    
                    if dir_items.intersection(DIR_ITEM_SET):
                        print "filepath now: "+filepath
                        MCS_FILE_EDITED = True
                        comment_position = get_position_to_comment(file)
                        createComment.create(
                            repo_name, repo_login, repo_owner, pr_number, author, commit_id, filepath, comment_position)

            if not MCS_FILE_EDITED:
                return RETURN_MSG
            else:
                sendStatus.send(0, repo_login, repo_name, head_sha_hash, "success")

        except Exception:
            # sending non-zero exit code for failure
            exc_type, exc_val, exc_tb = sys.exc_info()
            sendStatus.send(1, repo_login, repo_name, head_sha_hash, traceback.print_exception(exc_type, exc_val, exc_tb))

    else:
        print "request is not json"
        # sendStatus.send(2, repo_owner, repo_login, head_sha_hash, "failed")
        return RETURN_MSG

    return RETURN_MSG


if __name__ == "__main__":
    app.run(debug=True)
