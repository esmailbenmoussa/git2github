from migrator import Migrator
import os
from dotenv import load_dotenv

load_dotenv()

gh_handle = os.getenv("GH_HANDLE")  #
gh_token = os.getenv("GH_TOKEN")  #
gh_organization = os.getenv("GH_ORG")
git_server = "http://git@gitserver.mobileum.com/web/"
working_path = "/Users/esmailbenmoussa/Solidify/mobileum_migration"
migrator = Migrator(gh_handle, gh_token, gh_organization,
                    git_server, working_path)


if __name__ == '__main__':
    migrator.initializer()
