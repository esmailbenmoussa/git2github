import base64
from ftplib import FTP_PORT
import requests
from multiprocessing import Pool
import subprocess
import os
from json import load, dump, decoder
from status import StatusManager
status = StatusManager()


class Migrator:
    def __init__(self, gh_handle, gh_token, gh_organization, git_server, working_path):
        self.gh_base = f"{gh_organization}/"
        self.auth_header_gh = self._authorization_header_gh(gh_token)
        self.repo_list = self.load_json_file("roaming_git_repo_list.json")
        self.gh_repos = self._get_gh_repo()
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
                self.write_json("error", repo_name, error_msg)
                raise RuntimeError("command '{}' return with error (code {}): {}".format(
                    e.cmd, e.returncode, e.output))
        else:
            status.list(1, repo_name)
            try:
                subprocess.check_call(
                    ["git", "clone", "--bare", fr"{git_server}/{repo_name}.git", repo_name])
            except subprocess.CalledProcessError as e:
                error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                    e.cmd, e.returncode, e.output)))
                self.write_json("error", repo_name, error_msg)
                raise RuntimeError("command '{}' return with error (code {}): {}".format(
                    e.cmd, e.returncode, e.output))

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
            self.write_json("error", repo_name, error_msg)
            raise RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output))

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

    def write_json(self, file_name, repo_name, msg):
        with open(fr"/Users/esmailbenmoussa/Solidify/git2github/{file_name}.json", 'r+') as file:
            # First we load existing data into a dict.
            file_data = load(file)
            # Join new_data with file_data inside emp_details
            file_data[repo_name] = msg
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            dump(file_data, file)

    def _runner(self, repo):
        repo_name, repo_size = repo["name"], repo["size"]
        # gh_size = 999999999
        # if repo_name in gh_repos_names_size:
        #     gh_size = gh_repos_names_size[repo_name]
        status_file = self.load_json_file("status.json")
        if repo_name not in status_file:
            # if status_file.key(repo_name):
            status.list(0, repo_name, repo_size)
            self._git_clone_pull(repo_name)
            gh_repo = self._create_gh_repo(repo_name)
            if repo_size > 50000000:
                self.write_json("error", repo_name, "Too big repo")
            else:
                self._push_repo_gh(gh_repo, repo_name)
                status.list(4, repo_name, repo_size)
                self.write_json("status", repo_name, "migrated")
        else:
            print(repo_name, " Already migrated!")

    def initializer(self):
        delete_flag = False
        gh_repos_names_size = self.gh_repos["list"]
        # Deletes all repos in GitHub
        if delete_flag:
            pool = Pool()
            pool.map(self._delete_gh_repo, gh_repos_names_size.items())
        else:
            pool = Pool()
            pool.map(self._runner, self.repo_list)
