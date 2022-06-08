from stats import Analyzor
from migrator import Migrator
# from migrator_lfs import Migrator_LFS
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
# migrator_lfs = Migrator_LFS(gh_handle, gh_token, gh_organization,
#                             git_server, working_path)
# stats = Analyzor(gh_handle, gh_token, gh_organization,
#                  git_server, working_path)

if __name__ == '__main__':
    migrator.initializer()
    # migrator_lfs.initializer()
    # stats.initializer()
