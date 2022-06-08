import base64
from dataclasses import dataclass
import datetime
import logging
import requests
import time
from typing import Any, Callable, Dict, Iterable, Optional
from ftplib import FTP_PORT
from multiprocessing import Pool
import subprocess
import os
from json import load, dump
import re


class GitCommands:
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

    def push_tags(self, working_path, repo_name):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "push", "--tags", "origin"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})
            exit(1)

    def set_remote_url(self, working_path, repo_name, remote_url):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "remote", "set-url", "origin", remote_url])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})
            exit(1)

    def push_all(self, working_path, repo_name):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "push", "--all", "origin"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})
            exit(1)

    def clone_bare(self, working_path, git_server, repo_name):
        os.chdir(f"{working_path}")
        try:
            subprocess.check_call(
                ["git", "clone", "--bare", fr"{git_server}/{repo_name}.git", repo_name])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})
            raise RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output))

    def fetch(self, working_path, repo_name):
        os.chdir(f"{working_path}/{repo_name}")
        try:
            subprocess.check_call(
                ["git", "fetch"])
        except subprocess.CalledProcessError as e:
            error_msg = str(RuntimeError("command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output)))
            self.write_json("error", repo_name, {"msg": error_msg})
            exit(1)
