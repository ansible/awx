import argparse
import glob
import os
from shutil import move, copymode
from tempfile import mkstemp


def get_alias_depth(file_path, alias):
    if "src" not in file_path:
        raise Exception("src not found in file path")
    if not alias.startswith("@"):
        raise Exception("alias must start with '@'")

    name = alias.replace("@", "")

    if file_path.endswith(name):
        return 0
    if file_path.endswith(name + os.path.sep):
        return 0

    (head, tail) = os.path.split(file_path)

    if name in [n.replace(".jsx", "").replace(".js", "") for n in os.listdir(head)]:
        return 1

    max_depth = 30
    depth = 2
    while True:
        if depth > max_depth:
            raise Exception(f"({file_path}): max depth exceeded for {alias}")
        (head, tail) = os.path.split(head)
        if name in [n.replace(".jsx", "").replace(".js", "") for n in os.listdir(head)]:
            return depth
        depth += 1


def get_new_import_string(old_import_str, alias, alias_depth):
    if not alias.startswith("@"):
        raise Exception("alias must start with '@'")
    name = alias.replace("@", "")
    if alias_depth < 2:
        return old_import_str.replace(alias, "." + os.path.sep + name)
    new_segments = os.path.sep.join([".."] * (alias_depth - 1))
    return old_import_str.replace(alias, new_segments + os.path.sep + name)


aliases = [
    "@api",
    "@components",
    "@constants",
    "@contexts",
    "@screens",
    "@types",
    "@util",
    "@testUtils",
]


def find_and_replace_aliases(file_path, root_dir):
    fh, temp_path = mkstemp()

    has_logged_file_name = False
    with os.fdopen(fh, "w") as new_file:
        with open(file_path) as old_file:
            for (line_number, line) in enumerate(old_file):
                matched_alias = None
                for alias in aliases:
                    if alias in line:
                        matched_alias = alias
                        break
                if matched_alias:
                    alias_depth = get_alias_depth(file_path, matched_alias)
                    new_line = get_new_import_string(line, alias, alias_depth)
                    new_file.write(new_line)
                    if not has_logged_file_name:
                        log_file_replacement(root_dir, file_path)
                        has_logged_file_name = True
                    log_line_replacement(line_number, line, new_line)
                else:
                    new_file.write(line)
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
    args = parser.parse_args()
    return args


def run():
    args = parse_args()
    search_path = args.root_dir + "**/**/*.js*"

    for file_path in glob.iglob(search_path, recursive=True):
        find_and_replace_aliases(file_path, args.root_dir)


if __name__ == "__main__":
    run()
