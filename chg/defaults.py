from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import sys

CHG_PROJ_DIR = ".chg"
CHG_PROJ_DB_PATH = ".chg/db.sqlite3"

# for semantic search
CHG_PROJ_DB_TEXT = ".chg/db.txt"
CHG_PROJ_DB_VECTORS = ".chg/db.vec"
CHG_PROJ_FASTTEXT = ".chg/embeddings"
CHG_PROJ_FAISS = ".chg/faiss.db"

VARS = {
    "CHG_PROJ_DIR": CHG_PROJ_DIR,
    "CHG_PROJ_DB_PATH": CHG_PROJ_DB_PATH,
    "CHG_PROJ_DB_TEXT": CHG_PROJ_DB_TEXT,
    "CHG_PROJ_DB_VECTORS": CHG_PROJ_DB_VECTORS,
    "CHG_PROJ_FASTTEXT": CHG_PROJ_FASTTEXT,
    "CHG_PROJ_FAISS": CHG_PROJ_FAISS,
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
