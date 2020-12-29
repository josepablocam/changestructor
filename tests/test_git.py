import os

from chg.platform import git
# from pathlib.Path import tmp_path


def write(path, msg, mode="w"):
    with open(path, mode) as fout:
        fout.write(msg)


def test_add_file(tmp_path):
    curr_dir = os.getcwd()
    os.chdir(tmp_path)
    print(tmp_path)
    assert git.init() == 0
    write("file1.txt", "this is file 1")
    assert git.add(["."]) == 0
    assert git.commit("stub") == 0

    # new files
    write("file2.txt", "this is file 2")
    write("file3.txt", "this is file 3")
    assert git.add(["."]) == 0

    changed = git.diff_files()
    assert sorted(changed) == ["file2.txt", "file3.txt"]
    os.chdir(curr_dir)


def test_remove_files(tmp_path):
    curr_dir = os.getcwd()
    os.chdir(tmp_path)
    print(tmp_path)
    assert git.init() == 0
    write("file1.txt", "this is file 1")
    assert git.add(["."]) == 0
    assert git.commit("stub") == 0

    # remove files
    os.remove("file1.txt")
    assert git.add(["."]) == 0

    changed = git.diff_files()
    assert changed == ["file1.txt"]
    os.chdir(curr_dir)


def test_rename_files(tmp_path):
    curr_dir = os.getcwd()
    os.chdir(tmp_path)
    print(tmp_path)
    assert git.init() == 0
    write("file1.txt", "this is file 1")
    assert git.add(["."]) == 0
    assert git.commit("stub") == 0

    # remove files
    os.rename("file1.txt", "file1_renamed.txt")
    assert git.add(["."]) == 0

    changed = git.diff_files()
    assert changed == ["file1_renamed.txt"]

    os.chdir(curr_dir)


def test_modify_file(tmp_path):
    curr_dir = os.getcwd()
    os.chdir(tmp_path)
    print(tmp_path)
    assert git.init() == 0
    write("file1.txt", "this is file 1")
    assert git.add(["."]) == 0
    assert git.commit("stub") == 0

    # modify file 1
    write("file1.txt", "this is more content", mode="a")
    assert git.add(["."]) == 0

    changed = git.diff_files()
    assert changed == ["file1.txt"]

    os.chdir(curr_dir)
