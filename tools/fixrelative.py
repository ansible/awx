import argparse
import glob
import os
from shutil import move, copymode
from tempfile import mkstemp


def get_new_import_string(old_import_str, root):
    if not root.startswith("./"):
        raise Exception("root must start with './'")
    name = root.replace("./", "")

    left, right = old_import_str.split("from")
    left += "from '"

    _, trailing = right.split(name)
    return left + name + trailing


roots = [
    "./api",
    "./components",
    # "./constants",
    "./contexts",
    "./screens",
    "./types",
    "./util",
]


def get_root(line):
    matched_root = None
    for root in roots:
        if root in line:
            matched_root = root
            break
    if "jest" in line:
        matched_root = None
    return matched_root


def find_and_replace_roots(file_path, root_dir, preview):
    fh, temp_path = mkstemp()
    has_logged_file_name = False
    with os.fdopen(fh, "w") as new_file:
        with open(file_path) as old_file:
            for (line_number, line) in enumerate(old_file):
                matched_root = get_root(line)
                if matched_root:
                    new_line = get_new_import_string(line, matched_root)
                    if not preview:
                        new_file.write(new_line)
                    if not has_logged_file_name:
                        log_file_replacement(root_dir, file_path)
                        has_logged_file_name = True
                    log_line_replacement(line_number, line, new_line)
                elif not preview:
                    new_file.write(line)

    if not preview:
        copymode(file_path, temp_path)
        os.remove(file_path)
        move(temp_path, file_path)


def log_line_replacement(line_number, line, new_line):
    display_line = line.replace(os.linesep, "")
    display_new_line = new_line.replace(os.linesep, "")
    print(f"\t (line {line_number}): {display_line} --> {display_new_line}")


def log_file_replacement(root_dir, file_path):
    display_path = os.path.relpath(file_path, root_dir)
    print("")
    print(f"{display_path}:")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("root_dir", help="Root directory")
    parser.add_argument("--preview", help="Preview (no write)", action="store_true")
    args = parser.parse_args()
    return args


def run():
    args = parse_args()
    search_path = args.root_dir + "**/**/*.js*"

    for file_path in glob.iglob(search_path, recursive=True):
        find_and_replace_roots(file_path, args.root_dir, args.preview)


if __name__ == "__main__":
    run()
