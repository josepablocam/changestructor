import subprocess
import json


def run_command(cmd, **kwargs):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, **kwargs)
    stdout_output, _ = proc.communicate()
    stdout_output = stdout_output.decode().strip()
    return proc.returncode, stdout_output


def init():
    cmd = ["git", "init"]
    return run_command(cmd)[0]


def add(paths=None):
    if paths is not None:
        cmd = ["git", "add"] + paths
    else:
        cmd = ["git", "add", "-u"]
    return run_command(cmd)[0]


def diff(path=None, extra_flags=None):
    # get both cached (already staged) and uncached changes (i.e. not staged)
    cmd = ["git", "diff", "HEAD"]
    if extra_flags is None:
        extra_flags = ["--color=always"]
    cmd.extend(extra_flags)
    if path is not None:
        cmd.append(path)
    _, output = run_command(cmd)
    if len(output) == 0:
        return None
    else:
        return output


def cat(path, commit=None):
    if commit is None:
        commit = "HEAD"
    cmd = ["git", "show", commit + ":" + path]
    output = run_command(cmd)[1]
    return output


def diff_from_to(hash1, hash2):
    # after user has run git add
    cmd = ["git", "diff", "--color=always", hash1, hash2]
    _, output = run_command(cmd)
    if len(output) == 0:
        return None
    else:
        return output


def diff_files():
    # after user has run git add
    cmd = ["git", "diff", "HEAD", "--name-only"]
    _, output = run_command(cmd)
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
    return run_command(cmd)[0]


def hash():
    cmd = ["git", "rev-parse", "HEAD"]
    return run_command(cmd)[1]


def log():
    # parse logs (just hash and message)
    cmd = """
    git log \
  --pretty=format:'{^^^^date^^^^:^^^^%ci^^^^,^^^^abbreviated_commit^^^^:^^^^%h^^^^,^^^^subject^^^^:^^^^%s^^^^,^^^^body^^^^:^^^^%b^^^^}' \
  | sed 's/"/\\"/g' \
  | sed 's/\^^^^/"/g' \
  | jq -s '.'
    """
    output = run_command(cmd, shell=True)[1]
    return json.loads(output)


def root():
    cmd = ["git", "rev-parse", "--show-toplevel"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    output = output.decode().strip()
    return output


class LinesChanged(object):
    def __init__(self, path, source_lines, target_lines):
        self.path = path
        self.lines = (source_lines, target_lines)


def get_lines_changed(path):
    # don't provide contextual change lines, just what changed
    output = diff(path, extra_flags=["--unified=0"])
    change_annots = [
        line for line in output.split("\n") if line.startswith("@@")
    ]

    def parse_lines(v):
        lineno, _len = tuple(int(e) for e in v.split(",")
                             ) if "," in v else (int(v), 1)
        return [lineno + offset for offset in range(_len)]

    changes = []
    for annot in change_annots:
        # follows format: @@ -src_line[,src_len] +target_line[,target_len] @@
        # *_len counts include the *_line, if no len specified len=1
        # len=0 means insertion (there was not something there previously)
        parts = annot.split(" ")
        # drop the -/+
        src = parts[1][1:]
        target = parts[2][1:]
        source_lines = parse_lines(src)
        target_lines = parse_lines(target)
        change = LinesChanged(path, source_lines, target_lines)
        changes.append(change)
    return changes
