import subprocess
import json


def diff(path=None):
    # after user has run git add
    cmd = ["git", "diff", "--cached", "--color=always"]
    if path is not None:
        cmd.append(path)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    output = output.decode().strip()
    if len(output) == 0:
        return None
    else:
        return output


def diff_from_to(hash1, hash2):
    # after user has run git add
    cmd = ["git", "diff", "--color=always", hash1, hash2]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    output = output.decode().strip()
    if len(output) == 0:
        return None
    else:
        return output


def diff_files():
    # after user has run git add
    proc = subprocess.Popen(
        ["git", "diff", "--cached", "--name-only"],
        stdout=subprocess.PIPE,
    )
    output, _ = proc.communicate()
    output = output.decode().strip()
    if len(output) == 0:
        return []
    else:
        return output.split("\n")


def commit(msg, paths=None):
    # commit what is currently staged
    cmd = ["git", "commit"]
    if paths is not None:
        cmd.append("--only")
        cmd.extend(paths)
    cmd.extend(["-m", msg])
    proc = subprocess.Popen(cmd)
    proc.communicate()
    assert proc.returncode == 0, "Failed to commit"


def hash():
    cmd = ["git", "rev-parse", "HEAD"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    return output


def log():
    # parse logs (just hash and message)
    cmd = """
    git log \
  --pretty=format:'{^^^^date^^^^:^^^^%ci^^^^,^^^^abbreviated_commit^^^^:^^^^%h^^^^,^^^^subject^^^^:^^^^%s^^^^,^^^^body^^^^:^^^^%b^^^^}' \
  | sed 's/"/\\"/g' \
  | sed 's/\^^^^/"/g' \
  | jq -s '.'
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output, _ = proc.communicate()
    output = output.decode().strip()
    return json.loads(output)


def root():
    cmd = ["git", "rev-parse", "--show-toplevel"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    output = output.decode().strip()
    return output
