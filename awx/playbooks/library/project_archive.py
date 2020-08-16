ANSIBLE_METADATA = {
    "metadata_version": "1.0",
    "status": ["stableinterface"],
    "supported_by": "community",
}


DOCUMENTATION = """
---
module: project_archive
short_description: unpack a project archive
description:
  - Unpacks an archive that contains a project, in order to support handling versioned
    artifacts from (for example) GitHub Releases or Artifactory builds.
  - Handles projects in the archive root, or in a single base directory of the archive.
version_added: "2.9"
options:
  src:
    description:
    - The source archive of the project artifact
    required: true
  project_path:
    description:
    - Directory to write the project archive contents
    required: true
  force:
    description:
    - Files in the project_path will be overwritten by matching files in the archive
    default: False

author:
    - "Philip Douglass" @philipsd6
"""

EXAMPLES = """
- project_archive:
    src: "{{ project_path }}/.archive/project.tar.gz"
    project_path: "{{ project_path }}"
    force: "{{ scm_clean }}"
"""
