#!/usr/bin/env python
import errno    
import os
import shutil


def copy_if_exists(src, dst):
    if os.path.isfile(src):
        shutil.copy2(src, dst)


def ensure_directory_exists(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def run():
    collection_path = 'shippable/testresults'

    ensure_directory_exists(collection_path)

    copy_if_exists('/awx_devel/awx/ui/test/spec/reports/results.spec.xml', collection_path)
    copy_if_exists('/awx_devel/awx/ui/test/unit/reports/results.unit.xml', collection_path)


if __name__ == '__main__':
    run()
