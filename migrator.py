import base64
from ftplib import FTP_PORT
import requests
from multiprocessing import Pool, Process
import subprocess
import os
from json import load, dump
from status import StatusManager
from git_commands import GitCommands
import time
status = StatusManager()
git = GitCommands()


class Migrator:
    def __init__(self, gh_handle, gh_token, gh_organization, git_server, working_path):
        self.gh_base = f"{gh_organization}/"
        self.auth_header_gh = self._authorization_header_gh(gh_token)
        self.repo_list = self.load_json_file("roaming_git_repo_list.json")
        self.git_server = git_server
        self.working_path = working_path

    @staticmethod
    def _authorization_header_gh(pat: str) -> str:
        return "Basic " + base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")

    @staticmethod
    def _authorization_header_ado(pat: str) -> str:
        return "Basic " + base64.b64encode(f":{pat}".encode("ascii")).decode("ascii")

    @staticmethod
    def _authorization_header_gitlab(token: str) -> str:
        return "Bearer " + token

    def _git_clone_pull(self, repo_name):
        working_path = self.working_path
        git_server = self.git_server
        os.chdir(f"{working_path}")
        if(os.path.isdir(f"{working_path}/{repo_name}")):
            os.chdir(f"{working_path}/{repo_name}")
            status.list(1, repo_name)
            git.set_remote_url(self.working_path, repo_name,
                               fr"{git_server}/{repo_name}.git")
            git.fetch(self.working_path, repo_name)
        else:
            status.list(1, repo_name)
            git.clone_bare(self.working_path, git_server, repo_name)

        self.write_json("status", repo_name, {"level": 1, "check": True})

    def _push_repo_gh(self, gh_repo, repo_name):
        status.list(3, repo_name)
        working_path = self.working_path
        # New method
        os.chdir(f"{working_path}/{repo_name}")
        if "errors" in gh_repo:
            remote_url = fr"https://github.com/mobmigration/{repo_name}.git"
        else:
            remote_url = gh_repo["clone_url"]
        git.set_remote_url(self.working_path, repo_name, remote_url)
        git.push_all(self.working_path, repo_name)
        git.push_tags(self.working_path, repo_name)
        self.update_level_json("status", repo_name, {
                               "level": 3, "check": True})
        # raise RuntimeError("command '{}' return with error (code {}): {}".format(
        #     e.cmd, e.returncode, e.output))

    def _create_gh_repo(self, repo_name):
        status.list(2, repo_name)
        repo_details = {
            "name": f"{repo_name}",
            "description": "",
            "homepage": "",
            "visibility": "internal"
        }
        res = requests.post(
            f"{self.gh_base}repos",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
            json=repo_details,
        ).json()
        self.update_level_json("status", repo_name, {
                               "level": 2, "check": True})
        return res

    def _delete_gh_repo(self, repo):
        repo_name = repo[0]
        print(f"Deleting {repo_name}")
        requests.delete(
            f"https://api.github.com/repos/mobmigration/{repo_name}",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
        ).json()

    def _get_gh_repo(self):
        print("Getting gh repo")
        res = requests.get(
            f"{self.gh_base}repos?per_page=100",
            headers={
                "Authorization": self.auth_header_gh,
                "Content-Type": "application/json",
            },
        ).json()
        list = {}
        for item in res:
            list[item["name"]] = item["size"]
        response = {"res": res, "list": list}
        print("gh repo fetched")
        return response

    def _delete_local_repo(self, repo_name):
        os.chdir(self.working_path)
        subprocess.check_call(["rm", "-r", repo_name])

    def load_json_file(self, file_name: str):
        f = open(file_name)
        data = load(f)
        return data
        # with open(file_name, "a+") as f:
        #     try:
        #         data = load(f)
        #         return data
        #     except:
        #         obj = {}
        #         return obj

    def create_json(self, folder_name, repo_name, key, attr):
        with open(fr"/Users/esmailbenmoussa/Solidify/git2github/{folder_name}/{repo_name}.json", 'w+') as file:
            content = {fr"{repo_name}": {fr"{key}": attr}}
            dump(content, file)
            print("file created")

    def write_json(self, folder_name, repo_name, msg):
        with open(fr"/Users/esmailbenmoussa/Solidify/git2github/{folder_name}/{repo_name}.json", 'r+') as file:
            # First we load existing data into a dict.
            file_data = load(file)
            # Join new_data with file_data inside emp_details
            file_data[repo_name] = msg
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            dump(file_data, file)
            file.truncate()

    def update_level_json(self, folder_name, repo_name, msg):
        with open(fr"/Users/esmailbenmoussa/Solidify/git2github/{folder_name}/{repo_name}.json", 'r+') as file:
            # First we load existing data into a dict.
            file_data = load(file)
            # Join new_data with file_data inside emp_details
            file_data[fr"{repo_name}"] = msg
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            dump(file_data, file)
            file.truncate()

    def find(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return True
            else:
                return False

    def _error_manager(self, repo_name):
        path = "/Users/esmailbenmoussa/Solidify/git2github/error"
        find_file = self.find(fr"{repo_name}.json", path)
        if find_file is True:
            error_file = self.load_json_file(
                fr"/Users/esmailbenmoussa/Solidify/git2github/error/{repo_name}.json")
            if "msg" in error_file[repo_name]:
                exit(1)
            else:
                return True
        else:
            self.create_json("error", repo_name, "Initialize", "error")
            return True

    def _status_manager(self, repo_name):
        path = "/Users/esmailbenmoussa/Solidify/git2github/status"
        find_file = self.find(fr"{repo_name}.json", path)
        if find_file is True:
            status_file = self.load_json_file(
                fr"/Users/esmailbenmoussa/Solidify/git2github/status/{repo_name}.json")
            if "level" in status_file[repo_name]:
                progress_level = status_file[repo_name]["level"]
                print("Level:", progress_level)
                res = {"level": progress_level, "check": True}
                return res
            else:
                res = {"level": progress_level, "check": True}
                return res
        else:
            self.create_json("status", repo_name, "level", 0)
            res = {"level": 0, "check": True}
            return res

    def _runner(self, repo, gh_repo=""):
        repo_name = repo["name"]
        _error_manager = self._error_manager(repo_name)
        _status_manager = self._status_manager(repo_name)
        if _error_manager is True and _status_manager["check"] is True:
            if _status_manager["level"] < 4:
                if _status_manager["level"] == 0:
                    status.list(0, repo_name, 0)
                    self._git_clone_pull(repo_name)
                    self._runner(repo, gh_repo)
                if _status_manager["level"] == 1:
                    gh_repo = self._create_gh_repo(repo_name)
                    self._runner(repo, gh_repo)
                if _status_manager["level"] == 2:
                    if isinstance(gh_repo, dict):
                        self._push_repo_gh(gh_repo, repo_name)
                        self._runner(repo, gh_repo)
                    else:
                        gh_repo = {"errors": "errors"}
                        self._push_repo_gh(gh_repo, repo_name)
                        self._runner(repo, gh_repo)
                if _status_manager["level"] == 3:
                    status.list(4, repo_name, 0)
                    self.update_level_json("status", repo_name, {
                        "level": 4, "check": True})
                    self._runner(repo, gh_repo)
            else:
                # remote_url = fr"https://github.com/mobmigration/{repo_name}.git"
                # git.set_remote_url(self.working_path,
                #                    repo_name, remote_url)
                # git.push_tags(self.working_path, repo_name)
                print(repo_name, " Already migrated!")
        else:
            print(repo_name, "Other serius issue related to error/status report")

    def initializer(self):
        delete_flag = False
        # Deletes all repos in GitHub
        # if delete_flag:
        #     gh_repos = self._get_gh_repo()
        #     gh_repos_names_size = gh_repos["list"]
        #     pool = Pool()
        #     pool.map(self._delete_gh_repo, gh_repos_names_size.items())
        # else:
        pool = Pool()
        pool.map(self._runner, self.repo_list)
