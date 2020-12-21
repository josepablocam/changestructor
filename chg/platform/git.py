import subprocess


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
