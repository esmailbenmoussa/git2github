import base64
from ftplib import FTP_PORT
import requests
from multiprocessing import Pool, Process
import subprocess
import os
from json import load, dump, decoder, dumps
from status import StatusManager
import time
status = StatusManager()


class Analyzor:
    def __init__(self, gh_handle, gh_token, gh_organization, git_server, working_path):
        self.gh_base = f"{gh_organization}/"
        self.auth_header_gh = self._authorization_header_gh(gh_token)
        # self.repo_list = self.load_json_file("roaming_git_repo_list.json")
        # self.gh_repos = self._get_gh_repo()
        self.git_server = git_server
        self.working_path = working_path
        self.globalProps = {}
        self.list = {}

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
            subprocess.check_call(
                ["git", "remote", "set-url", "origin", fr"{git_server}/{repo_name}.git"])
            try:
                subprocess.check_call(["git", "fetch"])
            except subprocess.CalledProcessError as e:
                error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                    e.cmd, e.returncode, e.output)))
                self.write_json("error", repo_name, {"msg": error_msg})

        else:
            status.list(1, repo_name)
            try:
                subprocess.check_call(
                    ["git", "clone", "--bare", fr"{git_server}/{repo_name}.git", repo_name])
            except subprocess.CalledProcessError as e:
                error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                    e.cmd, e.returncode, e.output)))
                self.write_json("error", repo_name, {"msg": error_msg})
                raise RuntimeError("command '{}' return with error (code {}): {}".format(
                    e.cmd, e.returncode, e.output))

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
        subprocess.check_call(
            ["git", "remote", "set-url", "origin", remote_url])
        try:
            subprocess.check_call(["git", "push", "-u", "origin", "--all"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})
            exit(1)
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

    def write_json(self, folder_name, file_name, repo_name, msg):
        # with open(fr"/Users/esmailbenmoussa/Solidify/git2github/{folder_name}/{repo_name}.json", 'r+') as file:
        with open(fr"/Users/esmailbenmoussa/Solidify/git2github/{folder_name}/{file_name}.json", 'r+') as file:
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

    def initializer(self):
        print("HEJ")
        path = "/Users/esmailbenmoussa/Solidify/git2github"
        file_name = "result_migrated"
        find_file = self.find(fr"{file_name}.json", fr"{path}/result")
        if find_file is True:
            # os.chdir(fr"{path}/status")
            files = []
            for root, dirs, files in os.walk(fr"{path}/status"):
                files = files
            for file in files:
                status_file = self.load_json_file(
                    fr"{path}/status/{file}")
                name = file[0: -5]
                if "level" in status_file[name]:
                    progress_level = status_file[name]["level"]
                    print("Level:", progress_level)
                    if progress_level < 4:
                        result = {"level": progress_level}
                        self.write_json(
                            "result", "result_failed", name, result)
                    else:
                        result = "Migrated"
                        self.write_json(
                            "result", "result_migrated", name, result)

        else:
            self.create_json("result", file_name, "Initialize", "result")
            self.create_json("result", "result_failed", "Initialize", "result")
            return True
