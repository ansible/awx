#!/usr/bin/env python3
"""Prove backward compatibility of the docker-compose override refactor.

Validates that the old monolithic docker-compose.yml.j2 (at OLD_REF, the
commit before the refactor) and the new base-plus-override-files layout
produce identical effective compose configurations, by:

1. Rendering the old template with a fixed set of variables.
2. Rendering/collecting the new base + the overrides that
   `docker-compose-sources` would activate for the same variables,
   then merging them following the compose-spec merge rules
   (same alphabetical order as the Makefile's $(sort $(wildcard ...))).
3. Deep-diffing the two canonicalized configs across scenarios.

Also checks Makefile backward compatibility: every target that existed in
the root Makefile at OLD_REF must still exist (root Makefile or
tools/docker-compose/Makefile).

Run from anywhere inside the repo:  python3 tools/docker-compose/validate_compose.py
Requires: PyYAML, Jinja2, git.
"""
import copy
import json
import os
import re
import subprocess
import sys

import yaml
from jinja2 import Environment, StrictUndefined

OLD_REF = "d5e5ea3670"  # last commit before the override refactor

REPO = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"],
    cwd=os.path.dirname(os.path.abspath(__file__))).decode().strip()
TPL_DIR = "tools/docker-compose/ansible/roles/sources/templates"
STATIC_DIR = os.path.join(REPO, "tools/docker-compose/overrides")


def git_show(path, ref=OLD_REF):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=REPO).decode()


def render(src, variables):
    if src.startswith("#jinja2:"):
        src = src.split("\n", 1)[1]
    env = Environment(trim_blocks=True, lstrip_blocks=True,
                      keep_trailing_newline=True, undefined=StrictUndefined)
    env.filters["bool"] = lambda v: str(v).lower() in ("true", "1", "yes")
    env.filters["basename"] = os.path.basename
    return env.from_string(src).render(**variables)


# ---- compose-spec merge (the subset these files use) ----
def norm_depends(d):
    if isinstance(d, list):
        return {s: {"condition": "service_started"} for s in d}
    return copy.deepcopy(d)


def merge_service(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if k not in out:
            out[k] = copy.deepcopy(v)
        elif k == "volumes":  # merged by mount target
            by_tgt = {s.split(":")[1]: s for s in out[k]}
            for s in v:
                by_tgt[s.split(":")[1]] = s
            out[k] = list(by_tgt.values())
        elif k == "depends_on":
            merged = norm_depends(out[k])
            merged.update(norm_depends(v))
            out[k] = merged
        elif isinstance(v, dict):
            out[k] = {**out[k], **v}
        elif isinstance(v, list):
            out[k] = out[k] + [x for x in v if x not in out[k]]
        else:
            out[k] = v
    return out


def merge_compose(base, over):
    out = copy.deepcopy(base)
    for section in ("services", "volumes", "networks"):
        if section in over:
            tgt = out.setdefault(section, {}) or {}
            for name, cfg in (over[section] or {}).items():
                if section == "services" and name in tgt:
                    tgt[name] = merge_service(tgt[name], cfg)
                else:
                    tgt[name] = copy.deepcopy(cfg)
            out[section] = tgt
    return out


def canon(doc):
    doc = copy.deepcopy(doc)
    doc.pop("version", None)  # compose v2 ignores it; v1 is unsupported
    for svc in (doc.get("services") or {}).values():
        if "depends_on" in svc:
            svc["depends_on"] = norm_depends(svc["depends_on"])
        for key in ("volumes", "ports", "networks", "cap_add"):
            if key in svc and isinstance(svc[key], list):
                svc[key] = sorted(str(x) for x in svc[key])
        if "environment" in svc and isinstance(svc["environment"], dict):
            svc["environment"] = {k: str(v) for k, v in svc["environment"].items()}
    return doc


# ---- scenario runner ----
BASE_VARS = dict(
    awx_image="ghcr.io/ansible/awx_devel", awx_image_tag="devel",
    receptor_image="quay.io/ansible/receptor:devel",
    receptor_socket_file="/var/run/awx-receptor/receptor.sock",
    pg_username="awx", pg_database="awx", pg_password="pgpass",
    pg_hostname="", pg_port=5432, pg_tls=False,
    pgbouncer_port=6432, pgbouncer_max_pool_size=70,
    ansible_user_uid=1000, sign_work=False,
    control_plane_node_count=1, execution_node_count=0,
    minikube_container_group=False,
    enable_splunk=False, enable_prometheus=False, enable_grafana=False,
    enable_vault=False, vault_tls=False, enable_pgbouncer=False,
    enable_otel=False, enable_loki=False,
    install_editable_dependencies=False, editable_dependencies=[],
    ingress_path="/", api_urlpattern_prefix="",
    os_info={"stdout": "Linux"}, admin_password="adminpass",
    pg_log_min_duration_statement=1000, pg_max_connections=1024,
)


def active_overrides(v):
    """Mirror what roles/sources/tasks/main.yml puts into _sources/overrides/.

    Returns {filename: yaml_text}; the Makefile includes these via
    $(sort $(wildcard ...)), i.e. in filename order.
    """
    out = {}

    def static(name):
        with open(os.path.join(STATIC_DIR, f"{name}.yml")) as f:
            out[f"{name}.yml"] = f.read()

    def dynamic(name):
        with open(os.path.join(REPO, TPL_DIR, f"overrides/{name}.yml.j2")) as f:
            out[f"{name}.yml"] = render(f.read(), v)

    if v["enable_splunk"]:
        static("splunk")
    if v["enable_prometheus"]:
        static("prometheus")
    if v["enable_grafana"]:
        static("grafana")
    if v["enable_otel"]:
        static("otel")
    if v["enable_loki"]:
        static("loki")
    if v["minikube_container_group"]:
        static("minikube")
    if v["enable_pgbouncer"]:
        dynamic("pgbouncer")
    if v["enable_vault"]:
        dynamic("vault")
    if v["execution_node_count"] > 0:
        dynamic("execution-nodes")
    if v["install_editable_dependencies"] and v["editable_dependencies"]:
        dynamic("editable-deps")
    return out


def build_new(v):
    with open(os.path.join(REPO, TPL_DIR, "docker-compose.yml.j2")) as f:
        merged = yaml.safe_load(render(f.read(), v))
    for fname in sorted(active_overrides(v)):
        merged = merge_compose(merged, yaml.safe_load(active_overrides(v)[fname]))
    return canon(merged)


def build_old(v):
    return canon(yaml.safe_load(render(git_show(f"{TPL_DIR}/docker-compose.yml.j2"), v)))


def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"+ {path}/{k}: {json.dumps(b[k], default=str)[:200]}")
            elif k not in b:
                out.append(f"- {path}/{k}: {json.dumps(a[k], default=str)[:200]}")
            else:
                out += diff(a[k], b[k], f"{path}/{k}")
    elif a != b:
        out.append(f"~ {path}: OLD={a!r} NEW={b!r}")
    return out


SCENARIOS = {
    "defaults": {},
    "all_on_tls": dict(control_plane_node_count=2, execution_node_count=2,
                       enable_splunk=True, enable_prometheus=True, enable_grafana=True,
                       enable_vault=True, vault_tls=True, enable_pgbouncer=True,
                       enable_otel=True, enable_loki=True,
                       install_editable_dependencies=True,
                       editable_dependencies=["/home/u/dep-one", "/home/u/dep_two"],
                       minikube_container_group=True),
    "vault_no_tls": dict(enable_vault=True, vault_tls=False),
    "exec_nodes_only": dict(execution_node_count=3),
    "editable_only": dict(install_editable_dependencies=True,
                          editable_dependencies=["/x/awxkit"]),
    "pgbouncer_default_pghost": dict(pg_hostname=None, enable_pgbouncer=True),
}


def check_make_dry_runs():
    """`make -n` every shared docker target against the OLD_REF Makefile.

    Commands must match after collapsing whitespace, except for known
    intentional differences listed in ALLOWED.
    """
    ALLOWED = (
        # file was moved/modernized intentionally
        ("tools/docker-credential-plugins-override.yml",
         "tools/docker-compose/overrides/credential-plugins.yml"),
        # docker-clean is now correctly .PHONY; make words it differently
        ("'docker-clean' is up to date", "Nothing to be done for 'docker-clean'"),
        # docker-compose-sources installs the pre-commit hook on fresh clones
        ("", "ln -sf ../../pre-commit.sh"),
    )
    TARGETS = [
        "docker-compose-sources", "docker-compose", "docker-compose-up",
        "docker-compose-down", "docker-compose-credential-plugins",
        "docker-compose-test", "docker-compose-runtest",
        "docker-compose-build-schema", "docker-compose-clean",
        "docker-compose-container-group-clean", "docker-compose-build",
        "docker-compose-buildx", "docker-clean", "docker-clean-volumes",
        "docker-refresh", "docker-compose-container-group",
        "Dockerfile.dev", "awx-tui",
    ]

    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".mk", delete=False) as f:
        f.write(git_show("Makefile"))
        old_mk = f.name

    def dry_run(args):
        p = subprocess.run(["make", "-n"] + args, cwd=REPO,
                           capture_output=True, text=True)
        return [" ".join(l.split()) for l in p.stdout.splitlines() if l.strip()]

    def allowed(line_old, line_new):
        for a, b in ALLOWED:
            if (a and a in line_old and b in line_new.replace(a, b)) or \
               (not a and b in line_new):
                return True
            if a and b and line_old.replace(a, b) == line_new:
                return True
        return False

    bad = []
    for t in TARGETS:
        old = dry_run(["-f", old_mk, t])
        new = dry_run([t])
        if old == new:
            continue
        leftover_old = [l for l in old if l not in new]
        leftover_new = [l for l in new if l not in old]
        for lo, ln in zip(leftover_old, leftover_new):
            if not allowed(lo, ln):
                bad.append((t, lo, ln))
        for ln in leftover_new[len(leftover_old):]:
            if not allowed("", ln):
                bad.append((t, "<absent>", ln))
        for lo in leftover_old[len(leftover_new):]:
            bad.append((t, lo, "<absent>"))
    os.unlink(old_mk)
    print(f"=== make dry-runs: {'EQUIVALENT' if not bad else 'DIVERGED'} "
          f"({len(TARGETS)} targets compared) ===")
    for t, lo, ln in bad:
        print(f"    {t}:\n      OLD {lo}\n      NEW {ln}")
    return not bad


def check_make_targets():
    """Every target in the old root Makefile must still exist."""
    target_re = re.compile(r"^([A-Za-z0-9_.\/-]+)\s*:(?!=)", re.M)

    def targets(text):
        found = set()
        for name in target_re.findall(text):
            if name not in (".PHONY",) and "$" not in name and "%" not in name:
                found.add(name)
        return found

    old = targets(git_show("Makefile"))
    new = set()
    for mk in ("Makefile", "tools/docker-compose/Makefile"):
        with open(os.path.join(REPO, mk)) as f:
            new |= targets(f.read())
    missing = sorted(old - new)
    print(f"=== make targets: {'ALL PRESENT' if not missing else 'MISSING'} "
          f"({len(old)} old targets checked) ===")
    for t in missing:
        print("    missing:", t)
    return not missing


def main():
    ok = check_make_targets()
    ok = check_make_dry_runs() and ok
    for name, overrides_vars in SCENARIOS.items():
        v = {**BASE_VARS, **overrides_vars}
        if v.get("pg_hostname") is None:
            v.pop("pg_hostname")  # exercise the default('postgres') path
        d = diff(build_old(v), build_new(v))
        print(f"=== {name}: {'IDENTICAL' if not d else 'DIFFERENCES'} ===")
        for line in d:
            print("   ", line)
        ok = ok and not d
    print("RESULT:", "PASS — behavior preserved" if ok else "FAIL — behavior differs")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
