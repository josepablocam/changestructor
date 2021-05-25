from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
import sys

from chg.platform.git import root


def chg_path(p):
    return os.path.join(CHG_PROJ_DIR, p)


CHG_PROJ_DIR = os.path.join(root(), ".chg")
CHG_PROJ_DB_PATH = chg_path("db.sqlite3")

# for semantic search
CHG_PROJ_FAISS = chg_path("faiss.db")
CHG_PROJ_RANKER = chg_path("ranker.pkl")

VARS = {
    "CHG_PROJ_DIR": CHG_PROJ_DIR,
    "CHG_PROJ_DB_PATH": CHG_PROJ_DB_PATH,
    "CHG_PROJ_FAISS": CHG_PROJ_FAISS,
    "CHG_PROJ_RANKER": CHG_PROJ_RANKER,
}


def get_args():
    parser = ArgumentParser(
        description="Lookup default values for chg",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("var_name")
    return parser.parse_args()


def main():
    args = get_args()
    print(VARS.get(args.var_name, ""))
    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)
