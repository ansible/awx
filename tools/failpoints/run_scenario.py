#!/usr/bin/env python3
"""Run a failure scenario against the docker-compose dev cluster, then check invariants.

Runs on the host. It drives the cluster only through `docker exec ... awx-manage`, so it
needs no AWX install of its own. Start the cluster with at least two control nodes and one
execution node first, for example:

    MAIN_NODE_TYPE=control make docker-compose COMPOSE_TAG=devel \
        CONTROL_PLANE_NODE_COUNT=2 EXECUTION_NODE_COUNT=1

Then:

    tools/failpoints/run_scenario.py list
    tools/failpoints/run_scenario.py preflight
    tools/failpoints/run_scenario.py slow-controller --out /tmp/fp-runs

Every scenario first runs the preflight checks (mesh routes, receptor health, instance
state, failpoints enabled and none left armed, no leftover active jobs) and exits 2 without
starting anything if one fails, so an environment fault cannot produce an invalid run.

Each scenario prints a timeline, the failpoint hits, the adoption-related log lines and the
invariant results for the job, and exits non-zero if any invariant failed. With --out it
also saves the full timestamped container logs, every traceback, and a merged per-node
event timeline (UTC, ms) for the run.

Modes (--mode), for the scenarios that support both (slow-controller, event-queue,
cancel-orphan dead/deferred):
    timing  the original drive: sleeps (--lead, --backlog, --settle), docker kill/start at
            wall-clock moments, and waiting on heartbeat / is_lost timers.
    seam    every step is gated on a failpoint at a code seam instead: faults land after
            event counter --seam-counter (callback.event pause), backlogs are counted in
            events (--seam-backlog, callback_receiver.before_read), the lost-instance decision
            is forced and the heartbeat triggered explicitly (heartbeat.force_lost), adoptions
            are held before they are published (adoption.before_queue), and slow-controller's
            two finalizers run in a fixed --order (callback.artifacts).
Each run also writes metrics.json (outcome, magnitudes, key step timings, duration) next to
result.json.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(HERE, 'project')
PROJECT_NAME = 'failpoint_scenarios'
PLAYBOOKS = ('chatty.yml', 'quiet.yml', 'facts.yml', 'setstats.yml', 'bulk.yml', 'datacheck.yml', 'overlap.yml')
MARK = '@@FP@@'
T0 = time.monotonic()
EXEC_CONTAINER = 'tools_receptor_1'
RECEPTOR_SOCK = '/var/run/awx-receptor/receptor.sock'
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def utcnow():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def log(msg):
    print(f'[{time.monotonic() - T0:7.1f}s {utcnow()}] {msg}', flush=True)


def run(cmd, input=None, check=True, timeout=None):
    proc = subprocess.run(cmd, input=input, text=True, capture_output=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise RuntimeError(f'{" ".join(cmd)} failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}')
    return proc


def control_containers():
    out = run(['docker', 'ps', '--format', '{{.Names}}']).stdout.split()
    return sorted(n for n in out if re.fullmatch(r'tools_awx_\d+', n))


def container_for(hostname):
    """awx-1 -> tools_awx_1 (the docker-compose naming)."""
    return 'tools_' + hostname.replace('-', '_')


def manage(container, *args, check=True):
    if args[:2] == ('failpoint', 'wait'):
        # Waiting on a failpoint nobody armed blocks until the timeout, because an unarmed
        # failpoint records no hit. Fail at once instead of producing a stalled run.
        name = args[2]
        if name not in armed_names(container):
            raise RuntimeError(f'refusing to wait on failpoint {name!r}: it is not armed')
    return run(['docker', 'exec', '-i', container, 'awx-manage', *args], check=check)


def armed_names(container):
    out = run(['docker', 'exec', '-i', container, 'awx-manage', 'failpoint', 'list']).stdout
    return {row['name'] for row in json.loads(out[out.index('[') :])}


def orm(container, code):
    """Run Django code in a container; the code calls emit(obj) to return JSON."""
    prelude = f'import json\ndef emit(obj):\n    print({MARK!r} + json.dumps(obj, default=str))\n'
    out = run(['docker', 'exec', '-i', container, 'awx-manage', 'shell'], input=prelude + code).stdout
    for line in out.splitlines():
        if line.startswith(MARK):
            return json.loads(line[len(MARK) :])
    raise RuntimeError(f'no result from orm call:\n{out}')


def job_state(container, job_id):
    return orm(
        container,
        f'''
from django.db.models import Max
from django.utils.timezone import now
from awx.main.models import UnifiedJob
j = UnifiedJob.objects.get(pk={job_id}).get_real_instance()
last = j.get_event_queryset().aggregate(Max('created'))['created__max']
emit(dict(status=j.status, controller_node=j.controller_node, execution_node=j.execution_node,
          work_unit_id=j.work_unit_id, celery_task_id=j.celery_task_id, job_explanation=j.job_explanation,
          cancel_flag=j.cancel_flag,
          events=j.get_event_queryset().count(),
          last_event_age=(now() - last).total_seconds() if last else None))
''',
    )


def instances(container):
    return orm(
        container,
        '''
from awx.main.models import Instance
emit({i.hostname: dict(state=i.node_state, capacity=i.capacity, errors=i.errors, last_seen=i.last_seen,
                       node_type=i.node_type, enabled=i.enabled, adj=str(i.capacity_adjustment))
      for i in Instance.objects.all()})
''',
    )


def setting(container, name):
    return orm(container, f'from django.conf import settings\nemit(getattr(settings, {name!r}, None))\n')


def wait_for(desc, fn, timeout, poll=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = fn()
        except RuntimeError:
            result = None  # a container restarting mid-poll; try again
        if result:
            return result
        time.sleep(poll)
    raise TimeoutError(f'timed out after {timeout}s waiting for {desc}')


def wait_cluster_ready(container, hostnames, timeout=600):
    def ready():
        inst = instances(container)
        return all(inst.get(h, {}).get('state') == 'ready' and inst[h]['capacity'] for h in hostnames) and inst

    inst = wait_for(f'{", ".join(hostnames)} ready with capacity', ready, timeout, poll=10)
    for h in (h for h in hostnames if h.startswith('awx-')):
        wait_for(f'{h} receptor to see {EXEC_CONTAINER}', lambda: mesh_sees(container_for(h), 'receptor-1'), 180, poll=5)
    return inst


def receptor_status(container):
    out = run(['docker', 'exec', container, 'receptorctl', '--socket', RECEPTOR_SOCK, 'status', '--json'], check=False)
    try:
        return json.loads(out.stdout[out.stdout.index('{') :])
    except ValueError:
        return None


def preflight(containers, hostnames):
    """Check the environment before a run, so a broken cluster fails fast instead of
    producing a run that has to be thrown away. Returns a list of problems.

    Each check maps to a run that was invalid for that reason:
    - a control node reaching the execution node only through another control node
      (the dev mesh chain): a peer cannot adopt once the first node is down;
    - a control node's receptor not answering, AWX on that node not reaching it through
      receptor.conf (a clobbered config), or the execution node's receptor not listing work:
      adoption fails and reads as an adoption bug;
    - failpoints disabled: every arm is inert and the scenario injects nothing;
    - failpoints still armed from an earlier run: they fire in this one;
    - active jobs left over from an earlier run: they hold capacity and block launches.
    """
    problems = []
    control = {h for h in hostnames if h.startswith('awx-')}
    exec_nodes = [h for h in hostnames if h not in control]

    for host in sorted(control):
        status = receptor_status(container_for(host))
        if status is None:
            problems.append(f'{host}: receptor not answering on {RECEPTOR_SOCK}')
            continue
        routes = status.get('RoutingTable') or {}
        for node in exec_nodes:
            hop = routes.get(node)
            if hop is None:
                problems.append(f'{host}: no route to {node}')
            elif hop in control:
                problems.append(
                    f'{host}: reaches {node} only through control node {hop}; with {hop} down it cannot adopt. '
                    'Peer the hop node with every control node (receptor-hop.conf.j2).'
                )

    # receptorctl above talks to the socket directly; AWX instead reads the socket path from
    # /etc/receptor/receptor.conf. The dev bootstrap's write_receptor_config can rewrite that
    # bind-mounted file with a k8s-style config (wrong socket path) while the running receptor
    # keeps the old one, so receptorctl works and AWX does not (part 1 job 3, part 3 job 105).
    for container in containers:
        try:
            seen = orm(
                container,
                "from awx.main.tasks.receptor import get_receptor_ctl\n"
                "ctl = get_receptor_ctl()\n"
                "emit(sorted((ctl.simple_command('status').get('RoutingTable') or {}).keys()))\n",
            )
        except RuntimeError as exc:
            problems.append(f'{container}: AWX cannot reach its receptor via receptor.conf: {str(exc).strip()[-200:]}')
            continue
        missing = [n for n in exec_nodes if n not in seen]
        if missing:
            problems.append(f'{container}: AWX receptor connection sees no route to {", ".join(missing)}')

    out = run(['docker', 'exec', EXEC_CONTAINER, 'receptorctl', '--socket', RECEPTOR_SOCK, 'work', 'list'], check=False)
    if out.returncode != 0 or '{' not in out.stdout:
        problems.append(f'{EXEC_CONTAINER}: receptor work list failed: {(out.stdout + out.stderr).strip()[-200:]}')

    inst = instances(containers[0])
    for host in sorted(hostnames):
        i = inst.get(host)
        if i is None:
            problems.append(f'{host}: not registered as an instance')
        elif i['state'] != 'ready' or not i['capacity'] or i['errors']:
            problems.append(f'{host}: state={i["state"]} capacity={i["capacity"]} errors={i["errors"]!r}')

    for container in containers:
        if setting(container, 'AWX_FAILPOINTS_ENABLED') is not True:
            problems.append(f'{container}: AWX_FAILPOINTS_ENABLED is not true, so failpoints are inert')
    stale = armed_names(containers[0])
    if stale:
        problems.append(f'failpoints still armed from an earlier run: {", ".join(sorted(stale))} (awx-manage failpoint disarm --all)')

    active = orm(
        containers[0],
        """
from awx.main.constants import ACTIVE_STATES
from awx.main.models import UnifiedJob
emit(list(UnifiedJob.objects.filter(status__in=ACTIVE_STATES).values_list('id', 'status', 'name')))
""",
    )
    if active:
        problems.append('active jobs left over: ' + ', '.join(f'{i} {st} {n!r}' for i, st, n in active[:10]))
    return problems


def mesh_sees(container, node):
    """Is this control node's receptor up, with a route to node? A dead local receptor
    makes every adoption on that node fail, which would read as an adoption bug."""
    out = run(['docker', 'exec', container, 'receptorctl', '--socket', RECEPTOR_SOCK, 'status', '--json'], check=False)
    try:
        status = json.loads(out.stdout[out.stdout.index('{') :])
    except ValueError:
        return False
    return node in (status.get('RoutingTable') or {})


def unit_status(unit_id, container=EXEC_CONTAINER):
    """The work unit as a receptor node sees it (`work list`; this receptorctl has no `work status`)."""
    out = run(['docker', 'exec', container, 'receptorctl', '--socket', RECEPTOR_SOCK, 'work', 'list'], check=False)
    try:
        units = json.loads(out.stdout[out.stdout.index('{') :])
    except ValueError:
        return {'error': (out.stdout + out.stderr).strip()[-200:]}
    st = units.get(unit_id)
    if st is None:
        return {'error': 'unit not present'}
    return {k: st.get(k) for k in ('State', 'StateName', 'Detail', 'StdoutSize')}


def exec_node_processes(pattern):
    out = run(['docker', 'exec', EXEC_CONTAINER, 'ps', '-eo', 'pid,etimes,args'], check=False).stdout
    return [line.strip()[:160] for line in out.splitlines() if re.search(pattern, line)]


def setup(containers, jt_name, playbook, extra_vars, inventory='Demo Inventory', allow_simultaneous=False, instance_group=None, jt_fields=None):
    """Copy the scenario project to every control node and create the template once."""
    for c in containers:
        run(['docker', 'exec', c, 'mkdir', '-p', f'/var/lib/awx/projects/{PROJECT_NAME}'])
        for pb in PLAYBOOKS:
            run(['docker', 'cp', os.path.join(PROJECT_DIR, pb), f'{c}:/var/lib/awx/projects/{PROJECT_NAME}/{pb}'])
    return orm(
        containers[0],
        f'''
from awx.main.models import Organization, Inventory, Project, JobTemplate, NotificationTemplate
org = Organization.objects.get(name='Default')
from awx.main.models import InstanceGroup
inv = Inventory.objects.get(name={inventory!r})
proj, _ = Project.objects.get_or_create(name='failpoint scenarios',
    defaults=dict(organization=org, scm_type='', local_path={PROJECT_NAME!r}))
jt, _ = JobTemplate.objects.get_or_create(name={jt_name!r},
    defaults=dict(project=proj, inventory=inv, playbook={playbook!r}, organization=org))
jt.extra_vars = json.dumps({extra_vars!r})
jt.inventory = inv
jt.allow_simultaneous = {allow_simultaneous!r}
for k, v in {jt_fields or {}!r}.items():
    setattr(jt, k, v)
jt.save()
jt.instance_groups.clear()
if {instance_group!r}:
    jt.instance_groups.add(InstanceGroup.objects.get(name={instance_group!r}))
nt, _ = NotificationTemplate.objects.get_or_create(name='failpoint webhook', organization=org,
    notification_type='webhook',
    defaults=dict(notification_configuration={{'url': 'http://127.0.0.1:9/', 'headers': {{}},
        'http_method': 'POST', 'disable_ssl_verification': True, 'username': '', 'password': ''}}))
jt.notification_templates_success.add(nt)
jt.notification_templates_error.add(nt)
emit(dict(jt=jt.id))
''',
    )['jt']


def launch(container, jt_id):
    return orm(
        container,
        f'''
from awx.main.models import JobTemplate
job = JobTemplate.objects.get(pk={jt_id}).create_unified_job()
job.signal_start()
emit(job.id)
''',
    )


def start_job(containers, args, jt_name='failpoint chatty', playbook='chatty.yml', extra_vars=None, reset=True, allow_local=False, **setup_kw):
    """Reset failpoints, launch a job and wait until it runs remotely with a work unit."""
    c0 = containers[0]
    if reset:
        manage(c0, 'failpoint', 'disarm', '--all')
        manage(c0, 'failpoint', 'clear-hits')
    jt_id = setup(containers, jt_name, playbook, extra_vars or {'iterations': args.iterations}, **setup_kw)
    job_id = launch(c0, jt_id)
    log(f'launched job {job_id} from template {jt_id} ({playbook} {extra_vars or {"iterations": args.iterations}})')
    st = wait_for('job running with a work unit', lambda: (s := job_state(c0, job_id))['status'] == 'running' and s['work_unit_id'] and s, 300)
    log(f"job {job_id} running: controller={st['controller_node']} execution={st['execution_node']} unit={st['work_unit_id']}")
    if st['execution_node'] == st['controller_node'] and not allow_local:
        raise SystemExit('job executes on its own controller; start the cluster with MAIN_NODE_TYPE=control and an execution node')
    return job_id, st


def wait_finished(container, job_id, timeout):
    st = wait_for('job to finish', lambda: (s := job_state(container, job_id))['status'] not in ('pending', 'waiting', 'running') and s, timeout, poll=10)
    log(f"job {job_id} finished: status={st['status']} controller={st['controller_node']} explanation={st['job_explanation']!r}")
    return st


_REGISTRY = {}


def arm(container, name, action, match=None, nth=None, times=None, **opts):
    """awx-manage failpoint arm, with match given as a dict.

    A no-op recorder (sleep 0) for a failpoint this branch does not have is skipped: devel
    lacks the PR's seams, and a recorder only ever observes. Anything that injects still fails
    loudly on an unknown name.
    """
    if action == 'sleep' and float(opts.get('seconds', 1)) == 0:
        if container not in _REGISTRY:
            _REGISTRY[container] = registry(container)
        if name not in _REGISTRY[container]:
            log(f'not arming recorder {name}: this branch has no such failpoint')
            return
    cmd = ['failpoint', 'arm', name, '--action', action]
    for k, v in (match or {}).items():
        cmd += ['--match', f'{k}={v}']
    if nth is not None:
        cmd += ['--nth', str(nth)]
    if times is not None:
        cmd += ['--times', str(times)]
    for k, v in opts.items():
        cmd += [f'--{k}', str(v)]
    manage(container, *cmd)


def fired_hits(container, name):
    return json.loads(manage(container, 'failpoint', 'hits', name, '--fired').stdout)


def wait_hits(container, name, pred=None, count=1, timeout=300, poll=1, desc=None):
    """Wait until `count` fired hits of name satisfy pred(hit); return them."""

    def found():
        hs = [h for h in fired_hits(container, name) if pred is None or pred(h)]
        return hs if len(hs) >= count else None

    return wait_for(desc or f'{name} to fire', found, timeout, poll=poll)


def at_seconds(ts):
    """A hit's 'at' (or any ISO timestamp) as epoch seconds."""
    return datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp()


def wait_db_events(container, job_id, below):
    """Wait until every counter below `below` is stored: the receiver has drained them."""
    code = f'''
from awx.main.models import UnifiedJob
j = UnifiedJob.objects.get(pk={job_id}).get_real_instance()
emit(j.get_event_queryset().filter(counter__lt={below}).values('counter').distinct().count())
'''
    return wait_for(f'counters 1..{below - 1} stored', lambda: orm(container, code) == below - 1 or None, 120, poll=2)


def trigger_heartbeat(container):
    """Publish cluster_node_heartbeat to this node's own queue: a heartbeat now, not in up to 60 s."""
    return orm(
        container,
        '''
from awx.main.dispatch import get_task_queuename
from awx.main.tasks.system import cluster_node_heartbeat
cluster_node_heartbeat.apply_async(queue=get_task_queuename())
emit(get_task_queuename())
''',
    )


def guard_peer(container, job_id):
    """Seam: a peer may not claim this job (no lost-instance or sweep claim), so a slow restart
    of its controller cannot turn the scenario into a different one (the job-38 class)."""
    arm(container, 'lost_instance.before_claim', 'raise', {'job_id': job_id})
    arm(container, 'sweep.before_claim', 'raise', {'job_id': job_id})
    log(f'seam: peer claims of job {job_id} vetoed (lost_instance.before_claim / sweep.before_claim raise)')


def hold_at_counter(container, job_id, owner, counter):
    """Seam: hold the owner's job task before it handles event `counter`; return the hit."""
    arm(container, 'callback.event', 'pause', {'job_id': job_id, 'node': owner, 'counter': counter}, timeout=1800)
    hit = wait_hits(container, 'callback.event', lambda h: str(h['ctx'].get('counter')) == str(counter), timeout=600)[0]
    log(f'seam: {owner} holds job {job_id} before event counter {counter} (at {hit["at"]})')
    return hit


def job_metrics(container, job_id):
    """Outcome and magnitudes, straight from the DB."""
    return orm(
        container,
        f'''
from django.db import connection
from awx.main.models import UnifiedJob
j = UnifiedJob.objects.get(pk={job_id}).get_real_instance()
qs = j.get_event_queryset()
table = qs.model._meta.db_table
fk = qs.model.JOB_REFERENCE
with connection.cursor() as cur:
    cur.execute(f'SELECT counter, count(*) FROM {{table}} WHERE {{fk}} = %s AND job_created = %s GROUP BY counter HAVING count(*) > 1 ORDER BY counter', [j.id, j.created])
    dups = cur.fetchall()
def _body_status(body):
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except ValueError:
            return None
    return body.get('status') if isinstance(body, dict) else None
notes = [dict(status=_body_status(n.body), created=n.created) for n in j.notifications.all().order_by('created')]
emit(dict(status=j.status, explanation=j.job_explanation, controller=j.controller_node, cancel_flag=j.cancel_flag,
          started=j.started, finished=j.finished, stored=qs.count(), distinct=qs.values('counter').distinct().count(),
          dup_counters=len(dups), dup_extra_rows=sum(c - 1 for _, c in dups), dup_lo=dups[0][0] if dups else None,
          dup_hi=dups[-1][0] if dups else None,
          stats_rows=qs.filter(event='playbook_on_stats').count() if any(f.name == 'event' for f in qs.model._meta.fields) else None,
          notifications=len(notes), notification_statuses=[n['status'] for n in notes]))
''',
    )


def kill_and_restart(owner_container, peer_container, owner_host, wait_before_start=0):
    """Crash a control node the way a node failure does (SIGKILL to everything), then bring it back."""
    run(['docker', 'kill', owner_container])
    log(f'docker kill {owner_container}')
    if wait_before_start:
        time.sleep(wait_before_start)
    run(['docker', 'start', owner_container])
    log(f'docker start {owner_container}')
    wait_for(f'{owner_host} to answer awx-manage', lambda: manage(owner_container, 'failpoint', 'list', check=False).returncode == 0, 600, poll=10)
    log(f'{owner_host} is back (awx-manage answers)')


# --- Reporting --------------------------------------------------------------------------

# Log lines worth putting on the per-node timeline. Matched on ANSI-stripped text.
KEY_PATTERNS = [
    ('failpoint', r'Failpoint \S+ (fired|released|pausing)'),
    ('adopt', r'Adopting job|adoption (queued|deferred|skipped|failed)|Adoption (deferred|skipped|process phase failed)|adopt_job_async'),
    ('dedup', r'safe_threshold='),
    ('claim', r'Orphan sweep|Cross-controller adoption|already claimed'),
    ('finalize', r'finalized via|HADR_JOB_ADOPTION_TIMEOUT|orphaned for >'),
    ('detach', r'[Dd]etach'),
    ('release', r'[Rr]eleas(e|ing) work unit|work release|Failed to release|unknown work unit'),
    ('stall', r'stalled|abandoning the stream'),
    ('lost', r'marked as lost|Rejoining the cluster|Announced shutdown|Sweep-now|reaped'),
    ('health', r'Failed to connect to Redis|Health check'),
    ('stream', r'Cannot get receptor status|Failed to get work results|read operation|Unexpected EOF|stream'),
    ('exception', r'Traceback|IntegrityError|UniqueViolation|Error|Exception'),
    ('lifecycle', r'job_lifecycle|"state": "[a-z_]+"|\bstate[=:] ?\'?(running|successful|failed|error|canceled|finalize|finished)'),
    ('notify', r'[Nn]otification'),
    ('stats', r'playbook_on_stats|EOF event|event_processing_finished|final_counter'),
]


def save_logs(containers, since, out_dir):
    """Save `docker logs -t` for every container involved; return {container: [lines]}."""
    logs = {}
    for c in [*containers, EXEC_CONTAINER]:
        out = run(['docker', 'logs', '-t', '--since', since, c], check=False)
        text = ANSI.sub('', out.stdout + out.stderr)
        lines = sorted(text.splitlines())  # -t prefix sorts stdout and stderr together
        logs[c] = lines
        if out_dir:
            with open(os.path.join(out_dir, f'{c}.log'), 'w') as fh:
                fh.write('\n'.join(lines) + '\n')
    return logs


def tracebacks(logs):
    """Every traceback, with the log line that introduced it."""
    found = []
    for c, lines in logs.items():
        i = 0
        while i < len(lines):
            if 'Traceback (most recent call last)' in lines[i]:
                start = max(0, i - 1)
                j = i + 1
                while j < len(lines) and re.match(r'^\S+\s+(\s|File |\^|~)', lines[j]):
                    j += 1
                block = lines[start : j + 1]
                found.append((lines[i][:30], c, block))
                i = j + 1
            else:
                i += 1
    return sorted(found)


def key_events(logs, job_id, unit_id):
    ids = [rf'\b{job_id}\b']
    if unit_id:
        ids.append(re.escape(unit_id))
    id_re = re.compile('|'.join(ids))
    events = []
    for c, lines in logs.items():
        for line in lines:
            ts, _, rest = line.partition(' ')
            for kind, pat in KEY_PATTERNS:
                if re.search(pat, rest) and (id_re.search(rest) or kind in ('lost', 'health', 'failpoint')):
                    if 'HEAD / =>' in rest or 'GET /' in rest:
                        break
                    events.append((ts[:23] + 'Z', c.replace('tools_', ''), kind, rest.strip()[:260]))
                    break
    return sorted(events)


def db_timeline(container, job_id):
    return orm(
        container,
        f'''
from django.db.models import Min, Max
from awx.main.models import UnifiedJob
from awx.main.utils import failpoints
j = UnifiedJob.objects.get(pk={job_id}).get_real_instance()
rows = [('db', 'job created', j.created), ('db', 'job started', j.started), ('db', 'job finished (stored)', j.finished),
        ('db', 'job modified', j.modified)]
qs = j.get_event_queryset()
agg = qs.aggregate(first=Min('created'), last=Max('created'))
rows += [('db', 'first event row created', agg['first']), ('db', 'last event row created', agg['last'])]
has_event = any(f.name == 'event' for f in qs.model._meta.fields)
stats = list(qs.filter(event='playbook_on_stats').values_list('created', 'counter')) if has_event else []
for created, counter in stats:
    rows.append(('db', f'playbook_on_stats row (counter {{counter}})', created))
for n in j.notifications.all().order_by('created'):
    rows.append(('db', f'notification {{n.id}} subject={{n.subject!r}} status={{n.status}}', n.created))
for h in failpoints.hits(fired_only=True):
    rows.append((h['node'], f"failpoint {{h['name']}} fired action={{h['action']}} ctx={{h['ctx']}}", h['at']))
emit([(str(at), node, what) for node, what, at in rows if at])
''',
    )


def run_label(args):
    if args.scenario in ('data-check', 'stats-insert-race', 'same-hosts', 'few-workers', 'disable-live', 'capacity-race'):
        parts = [args.scenario, getattr(args, 'branch', '') or 'unknown'] + ([args.variant] if args.variant else [])
        if args.variant in ('slow', 'streams') and args.mode == 'seam':
            parts.append(args.order)
        if args.fail_host:
            parts.append('failhost')
        if args.constructed:
            parts.append('constructed')
        return '-'.join(parts)
    parts = [args.scenario]
    if args.scenario in VARIANTS:
        parts.append(args.variant)
    if args.scenario == 'claim-race' and args.cancel_in_adoption:
        parts.append('cancel')
    if args.scenario == 'adopter-dies':
        parts.append(args.hold_at)
    if args.scenario in ('event-queue', 'hybrid-resume'):
        parts.append(args.trigger)
    parts.append(args.mode)
    if (args.scenario == 'slow-controller' or (args.scenario in ('workflow-orphan', 'set-stats-artifacts') and args.variant == 'slow')) and args.mode == 'seam':
        parts.append(args.order)
    return '-'.join(parts)


def report(containers, job_id, since, args, unit_id=None, notes=(), metrics=None, from_logs=None, out_name=None):
    """Print and save everything about one job. from_logs(logs) -> dict adds log-derived
    metrics; out_name overrides the artifact directory name (several jobs in one run)."""
    alive = [c for c in containers if manage(c, 'failpoint', 'list', check=False).returncode == 0]
    c = alive[0]
    hits = json.loads(manage(c, 'failpoint', 'hits', '--fired').stdout)
    result = json.loads(manage(c, 'failpoint', 'check-job', str(job_id)).stdout)
    out_dir = None
    if args.out:
        out_dir = os.path.join(args.out, out_name or f'{run_label(args)}-job{job_id}')
        os.makedirs(out_dir, exist_ok=True)
    logs = save_logs(containers, since, out_dir)
    print('\n=== Failpoint hits that fired ===')
    for h in hits:
        print(f"  {h['at']}  {h['name']:<40} node={h['node']} action={h['action']} ctx={h['ctx']}")
    print('\n=== DB timeline (UTC) ===')
    for at, node, what in sorted(db_timeline(c, job_id)):
        print(f'  {at}  {node:<6} {what}')
    print('\n=== Key log events (UTC, from docker logs -t) ===')
    events = key_events(logs, job_id, unit_id)
    for ts, node, kind, text in events[: args.max_lines]:
        print(f'  {ts}  {node:<10} {kind:<9} {text}')
    if len(events) > args.max_lines:
        print(f'  ... {len(events) - args.max_lines} more (see saved logs)')
    print('\n=== Tracebacks ===')
    tbs = tracebacks(logs)
    for ts, cont, block in tbs:
        print(f'  --- {cont} {ts}')
        for line in block[-8:]:
            print('    ' + line[:240])
    if not tbs:
        print('  none')
    for note in notes:
        print(f'\nNOTE: {note}')
    print(f"\n=== Invariants for job {job_id} (status={result['status']}, controller={result['controller_node']}) ===")
    print(f"  job_explanation: {result['job_explanation']!r}")
    for chk in result['checks']:
        print(f"  [{'PASS' if chk['ok'] else 'FAIL'}] {chk['name']:<24} {chk['detail']}")
    if metrics is not None:
        metrics = dict(metrics, job_id=job_id, label=run_label(args), mode=args.mode)
        metrics.update(job_metrics(c, job_id))
        metrics['failed_invariants'] = sorted(chk['name'] for chk in result['checks'] if not chk['ok'])
        metrics['tracebacks'] = len(tbs)
        if from_logs:
            metrics.update(from_logs(logs))
        metrics['duration_s'] = round(time.monotonic() - T0, 1)
        print('\n=== Metrics ===')
        print(json.dumps(metrics, indent=2, default=str))
    if out_dir:
        with open(os.path.join(out_dir, 'result.json'), 'w') as fh:
            json.dump({'job_id': job_id, 'hits': hits, 'result': result, 'events': events, 'tracebacks': tbs}, fh, indent=2, default=str)
        if metrics is not None:
            with open(os.path.join(out_dir, 'metrics.json'), 'w') as fh:
                json.dump(metrics, fh, indent=2, default=str)
        print(f'\nartifacts: {out_dir}')
    return result


def since_now():
    # The Z matters: without it docker reads the timestamp as the host's local time.
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


# --- Scenarios --------------------------------------------------------------------------


def scenario_slow_controller(containers, args):
    """Dup notifications: a controller misses heartbeats but stays alive while a peer adopts.

    1. Launch a long, chatty job and note its controller C.
    2. Pause every periodic heartbeat on C. C keeps streaming the job; only its last_seen
       goes stale.
    3. Wait for a peer to claim the job through the lost-instance path.
    4. Release C's heartbeat so both controllers are alive and both own the job's stream.
    5. Let the job finish and check invariants.

    --mode seam replaces the timers and the finalize race with seams:
      2a. C's job task is held before event --seam-counter (callback.event), so the adopter's
          dedup snapshot is exactly counter-1 instead of "whatever was stored at claim time".
      3.  The peer's lost check is forced (heartbeat.force_lost trigger) and its heartbeat
          published now, instead of waiting for C's last_seen to age past is_lost.
      5.  The second finalizer of --order is held at the start of its end-of-run processing
          (callback.artifacts) until the first has finalized and released the unit.
    --fresh-event-queries deletes the EventQuery rows first, so both finalizers race to insert
    them (the IntegrityError that made job 1 'error').
    """
    if len(containers) < 2:
        raise SystemExit('slow-controller needs at least two control nodes')
    c0 = containers[0]
    seam = args.mode == 'seam'
    since = since_now()
    if args.fresh_event_queries:
        n = orm(c0, 'from awx.main.models.event_query import EventQuery\nemit(EventQuery.objects.all().delete()[0])\n')
        log(f'deleted {n} EventQuery rows: both finalizers will try to create them')
    job_id, st = start_job(containers, args)
    owner = st['controller_node']
    peer = next(c for c in containers if c != container_for(owner))
    peer_host = container_for_host(peer)
    m = {'owner': owner, 'peer': peer_host}
    # Recording only (sleep 0), in both modes: when each side snapshots and finalizes.
    for name in ('adoption.after_snapshot', 'job.after_finalize_before_release', 'adoption.after_finalize_before_release'):
        arm(c0, name, 'sleep', {'job_id': job_id}, seconds=0)
    second = None
    if seam:
        # Armed before the claim: an adopter that replays a short job can reach the end of the
        # stream within a second of its snapshot.
        second = owner if args.order == 'adopter-first' else peer_host
        arm(c0, 'callback.artifacts', 'pause', {'job_id': job_id, 'node': second}, timeout=1800)
        log(f'seam: {second} will hold its end-of-run processing (order {args.order})')
        hold_at_counter(c0, job_id, owner, args.seam_counter)
        wait_db_events(c0, job_id, args.seam_counter)
    else:
        arm(c0, 'callback.artifacts', 'sleep', {'job_id': job_id}, seconds=0)

    manage(c0, 'failpoint', 'arm', 'heartbeat.start', '--action', 'pause', '--match', f'node={owner}', '--match', 'periodic=True', '--timeout', '1200')
    log(f'armed heartbeat.start pause on {owner}')
    hb = json.loads(manage(c0, 'failpoint', 'wait', 'heartbeat.start', '--timeout', '120').stdout)
    m['heartbeat_paused_at'] = hb['at']
    log(f'{owner} heartbeat is paused; waiting for a peer to claim job {job_id}')

    notes = []
    try:
        if seam:
            arm(c0, 'heartbeat.force_lost', 'trigger', {'node': peer_host, 'other': owner})
            log(f'seam: {peer_host} will treat {owner} as lost on its next heartbeat; triggering one now ({trigger_heartbeat(peer)})')
        snap = wait_hits(c0, 'adoption.after_snapshot', timeout=args.claim_timeout, desc='a peer to claim and snapshot the job')[0]
        m['claim_snapshot_at'] = snap['at']
        m['claim_node'] = snap['node']
        m['safe_threshold'] = int(snap['ctx']['safe_threshold'])
        m['claim_delay_s'] = round(at_seconds(snap['at']) - at_seconds(hb['at']), 1)
        log(f"job {job_id} claimed by {snap['node']}: snapshot safe_threshold={m['safe_threshold']}, {m['claim_delay_s']}s after the heartbeat pause")
        if seam:
            manage(c0, 'failpoint', 'disarm', 'heartbeat.force_lost')
            manage(c0, 'failpoint', 'disarm', 'callback.event')
            log(f'seam: released {owner} at counter {args.seam_counter}')
    except TimeoutError as exc:
        notes.append(f'no peer claimed the job: {exc}')
        m['invalid'] = 'no claim'
        log(notes[-1])
        if seam:
            manage(c0, 'failpoint', 'disarm', 'callback.event')
    finally:
        manage(peer, 'failpoint', 'release', 'heartbeat.start', check=False)
        manage(peer, 'failpoint', 'disarm', 'heartbeat.start', check=False)
        log(f'released {owner} heartbeat; both controllers are live again')

    if seam and second:
        first_hit = 'job.after_finalize_before_release' if second == peer_host else 'adoption.after_finalize_before_release'
        try:
            h = wait_hits(c0, first_hit, timeout=args.finish_timeout, poll=3)[0]
            log(f'seam: first finalizer done ({first_hit} on {h["node"]} at {h["at"]}); releasing {second}')
        except TimeoutError as exc:
            notes.append(f'first finalizer never reached {first_hit}: {exc}')
            log(notes[-1])
        manage(c0, 'failpoint', 'disarm', 'callback.artifacts')

    wait_finished(c0, job_id, args.finish_timeout)
    log(f'waiting {args.settle}s for callback receivers and notifications to settle')
    time.sleep(args.settle)
    fin = {h['name']: h for name in ('job.after_finalize_before_release', 'adoption.after_finalize_before_release') for h in fired_hits(c0, name)[:1]}
    if len(fin) == 2:
        a, b = sorted(fin.values(), key=lambda h: at_seconds(h['at']))
        m['first_finalizer'] = f"{a['node']} ({'job task' if a['name'].startswith('job.') else 'adoption'})"
        m['finalize_gap_ms'] = round((at_seconds(b['at']) - at_seconds(a['at'])) * 1000)
    elif fin:
        h = next(iter(fin.values()))
        m['first_finalizer'] = f"{h['node']} ({'job task' if h['name'].startswith('job.') else 'adoption'}) only"
    arts = sorted(fired_hits(c0, 'callback.artifacts'), key=lambda h: at_seconds(h['at']))
    if len(arts) >= 2 and not seam:
        m['artifacts_order'] = [h['node'] for h in arts]
        m['artifacts_gap_ms'] = round((at_seconds(arts[1]['at']) - at_seconds(arts[0]['at'])) * 1000)
    m['adoptions'] = len(fired_hits(c0, 'adoption.after_snapshot'))
    m['streams'] = 1 + m['adoptions']
    return report(containers, job_id, since, args, st['work_unit_id'], notes, metrics=m)


def scenario_finalize_strand(containers, args):
    """Finalize strand: adoption finalization raises; is the unit released under a 'running' job?

    1. Launch a chatty job and note its controller C.
    2. Arm adoption.before_finalize (raise, once, this job only).
    3. Crash C (docker kill) and start it again. C's startup heartbeat re-adopts its own job
       (same-controller adoption); with --adopt-via peer, C stays down until a peer claims it.
    4. The adoption streams to the end and raises at finalization.
    5. Watch the job, its work unit and the adopter's heartbeats for --observe seconds.
    """
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)

    manage(peer, 'failpoint', 'arm', 'adoption.before_finalize', '--action', 'raise', '--match', f'job_id={job_id}', '--times', '1')
    log('armed adoption.before_finalize raise (times=1)')
    time.sleep(args.lead)

    if args.adopt_via == 'peer':
        run(['docker', 'kill', oc])
        log(f'docker kill {oc}; waiting for a peer to claim job {job_id}')
        st = wait_for('a peer to claim the job', lambda: (s := job_state(peer, job_id))['controller_node'] != owner and s, args.claim_timeout)
        log(f"job {job_id} claimed by {st['controller_node']}")
        run(['docker', 'start', oc])
        log(f'docker start {oc}')
    else:
        kill_and_restart(oc, peer, owner)

    hit = json.loads(manage(peer, 'failpoint', 'wait', 'adoption.before_finalize', '--timeout', str(args.finish_timeout)).stdout)
    log(f"adoption.before_finalize fired on {hit['node']} at {hit['at']}")

    notes = []
    last = None
    deadline = time.monotonic() + args.observe
    while time.monotonic() < deadline:
        s = job_state(peer, job_id)
        u = unit_status(unit)
        snap = (s['status'], s['controller_node'], s['work_unit_id'], s['job_explanation'], json.dumps(u, sort_keys=True))
        if snap != last:
            log(
                f"job {job_id}: status={s['status']} controller={s['controller_node']} unit={s['work_unit_id']} "
                f"explanation={s['job_explanation']!r} last_event_age={s['last_event_age']}s; exec-node unit: {u}"
            )
            last = snap
        if s['status'] not in ('running', 'waiting', 'pending'):
            break
        time.sleep(15)
    s = job_state(peer, job_id)
    notes.append(f"after observing {args.observe}s: status={s['status']} explanation={s['job_explanation']!r} exec-node unit={unit_status(unit)}")
    log(notes[-1])
    manage(peer, 'failpoint', 'disarm', '--all')
    return report(containers, job_id, since, args, unit, notes)


def scenario_quiet_deadline(containers, args):
    """Quiet deadline: a healthy job in a long silent task is failed on its first adoption deferral.

    Needs HADR_JOB_ADOPTION_TIMEOUT shorter than --quiet (e.g. 120 in local_settings.py).
    1. Launch quiet.yml: three events, a --quiet second silent task, three more events.
    2. Wait until the last stored event is older than HADR_JOB_ADOPTION_TIMEOUT.
    3. Arm adoption.unit_status (raise, once): the adopter's first unit-status query fails,
       which is what a transient receptor/mesh error looks like to adopt_job_async.
       --no-inject skips this, to show the control case.
    4. Crash the controller (docker kill) and start it again so it re-adopts the job.
    5. Watch the job and whether its work unit and playbook keep running.
    """
    c0 = containers[0]
    timeout = setting(c0, 'HADR_JOB_ADOPTION_TIMEOUT')
    log(f'HADR_JOB_ADOPTION_TIMEOUT={timeout}')
    if timeout is None or timeout + 30 > args.quiet:
        raise SystemExit(f'HADR_JOB_ADOPTION_TIMEOUT={timeout} must be well under --quiet={args.quiet}; override it in local_settings.py')
    since = since_now()
    job_id, st = start_job(containers, args, jt_name='failpoint quiet', playbook='quiet.yml', extra_vars={'quiet_seconds': args.quiet})
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)

    s = wait_for(
        f'last event older than {timeout}s',
        lambda: (s := job_state(c0, job_id))['last_event_age'] is not None and s['last_event_age'] > timeout + 10 and s,
        timeout + 240,
        poll=10,
    )
    log(f"job {job_id}: {s['events']} events, last one {s['last_event_age']:.0f}s ago; playbook: {exec_node_processes(r'sleep ' + str(args.quiet))}")
    if not args.no_inject:
        manage(peer, 'failpoint', 'arm', 'adoption.unit_status', '--action', 'raise', '--match', f'job_id={job_id}', '--times', '1')
        log('armed adoption.unit_status raise (times=1): first unit status query of the adoption fails')

    kill_and_restart(oc, peer, owner)

    notes = []
    last = None
    end = time.monotonic() + args.quiet + 180
    reaped_at = None
    while time.monotonic() < end:
        s = job_state(peer, job_id)
        u = unit_status(unit)
        procs = exec_node_processes(r'sleep ' + str(args.quiet))
        snap = (s['status'], s['controller_node'], s['job_explanation'], u.get('StateName'), u.get('error'), bool(procs))
        if snap != last:
            log(
                f"job {job_id}: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r} "
                f"events={s['events']}; exec-node unit: {u}; playbook sleep running: {bool(procs)}"
            )
            last = snap
        if s['status'] not in ('running', 'waiting', 'pending') and reaped_at is None:
            reaped_at = time.monotonic()
            notes.append(
                f"job terminal at {utcnow()} status={s['status']} explanation={s['job_explanation']!r}; exec-node unit then: {u}; sleep running: {procs}"
            )
        if reaped_at is not None and u.get('StateName') in ('Succeeded', 'Failed', 'Canceled') and not procs:
            break
        if reaped_at is not None and 'error' in u and not procs:
            break
        time.sleep(15)
    s = job_state(peer, job_id)
    notes.append(f"end of observation {utcnow()}: status={s['status']} events={s['events']} exec-node unit={unit_status(unit)}")
    log(notes[-1])
    manage(peer, 'failpoint', 'disarm', '--all')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes)


def scenario_self_unavailable(containers, args):
    """Self unavailable: a live controller marks itself UNAVAILABLE for one heartbeat mid-job.

    1. Launch a chatty job and note its controller C.
    2. Arm health_check.redis_ping on C to raise redis ConnectionError --outages times: C's
       next heartbeat records 'Failed to connect to Redis' and sets itself UNAVAILABLE with
       capacity 0, exactly as a real Redis blip would, and recovers on the heartbeat after.
       Nothing else on C is disturbed: it keeps streaming the job.
    3. Watch whether a peer claims the job while C is still streaming it.
    4. Let the job finish and check invariants.
    """
    c0 = containers[0]
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    time.sleep(args.lead)

    manage(
        c0,
        'failpoint',
        'arm',
        'health_check.redis_ping',
        '--action',
        'raise',
        '--exception',
        'redis.exceptions.ConnectionError',
        '--match',
        f'node={owner}',
        '--times',
        str(args.outages),
    )
    log(f'armed health_check.redis_ping raise ConnectionError on {owner} (times={args.outages})')
    wait_for(f'{owner} to mark itself unavailable', lambda: instances(c0)[owner]['state'] == 'unavailable', 150, poll=2)
    log(f'{owner} is unavailable: {instances(c0)[owner]}')
    notes = []
    try:
        s = wait_for('a peer to claim the job', lambda: (s := job_state(c0, job_id))['controller_node'] != owner and s, args.claim_timeout, poll=3)
        log(f"job {job_id} claimed by {s['controller_node']} while {owner} is {instances(c0)[owner]['state']}")
    except TimeoutError as exc:
        notes.append(f'no peer claimed the job: {exc}')
        log(notes[-1])
    wait_for(f'{owner} to recover', lambda: instances(c0)[owner]['state'] == 'ready', 200, poll=5)
    log(f'{owner} is ready again')
    manage(c0, 'failpoint', 'disarm', 'health_check.redis_ping')

    wait_finished(c0, job_id, args.finish_timeout)
    log(f'waiting {args.settle}s for callback receivers and notifications to settle')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes)


# --- Helpers for the second batch of scenarios -------------------------------------------


def is_pr_branch(container):
    """The PR branch registers the cross-controller failpoints; devel does not."""
    return 'sweep.before_claim' in manage(container, 'failpoint', 'registry').stdout


def cancel_job(container, job_id):
    """UnifiedJob.cancel() from this container, recording where the cancel was addressed."""
    return orm(
        container,
        f'''
import io, logging
from django.utils.timezone import now
from awx.main.models import UnifiedJob
buf = io.StringIO()
handler = logging.StreamHandler(buf)
logging.getLogger('awx.main.models.unified_jobs').addHandler(handler)
logging.getLogger('awx.main.models.unified_jobs').setLevel(logging.INFO)
j = UnifiedJob.objects.get(pk={job_id})
before = dict(controller_node=j.controller_node, celery_task_id=j.celery_task_id, status=j.status)
at = now()
flag = j.cancel()
emit(dict(at=at, returned=flag, sent_to=before, log=buf.getvalue().strip()))
''',
    )


def set_instance(container, hostname, **fields):
    assignments = '\n'.join(f'i.{k} = {v!r}' for k, v in fields.items())
    return orm(
        container,
        f'''
from decimal import Decimal
from awx.main.models import Instance
i = Instance.objects.get(hostname={hostname!r})
{assignments}
i.save(update_fields={list(fields)!r})
emit(dict(hostname=i.hostname, **{{k: str(getattr(i, k)) for k in {list(fields)!r}}}))
''',
    )


def redis_backlog(container):
    return orm(
        container,
        'from django.conf import settings\nfrom awx.main.utils.redis import get_redis_client\nemit(get_redis_client().llen(settings.CALLBACK_QUEUE))\n',
    )


def watch(container, job_id, unit, seconds, until=None, poll=10, label='job', extra=None):
    """Print every change of the job's key fields and its exec-node unit; stop when until(state) is true."""
    last = None
    end = time.monotonic() + seconds
    s = None
    while time.monotonic() < end:
        try:
            s = job_state(container, job_id)
        except RuntimeError:
            time.sleep(poll)
            continue
        u = unit_status(unit) if unit else {}
        more = extra() if extra else None
        snap = (
            s['status'],
            s['controller_node'],
            s['celery_task_id'],
            s['cancel_flag'],
            s['job_explanation'],
            u.get('StateName'),
            u.get('error'),
            json.dumps(more, default=str),
        )
        if snap != last:
            log(
                f"{label} {job_id}: status={s['status']} controller={s['controller_node']} task={s['celery_task_id']} cancel_flag={s['cancel_flag']} "
                f"events={s['events']} explanation={s['job_explanation']!r}; exec-node unit: {u}" + (f'; {more}' if more is not None else '')
            )
            last = snap
        if until and until(s):
            return s
        time.sleep(poll)
    return s


def terminal(s):
    return s['status'] not in ('pending', 'waiting', 'running')


def start_back(container, host):
    run(['docker', 'start', container], check=False)
    log(f'docker start {container}')
    wait_for(f'{host} to answer awx-manage', lambda: manage(container, 'failpoint', 'list', check=False).returncode == 0, 600, poll=10)
    log(f'{host} is back (awx-manage answers)')


# --- cancel --------------------------------------------------------------------------------


def scenario_cancel_orphan(containers, args):
    """Cancel: a cancel issued while the job is orphaned, being claimed, or deferred.

    UnifiedJob.cancel() commits cancel_flag and then sends a dispatcher 'cancel' for
    celery_task_id on controller_node's pg_notify channel. Only a dispatcher worker running a
    task with that uuid can act on it. Variants (--variant):
      dead            controller killed and left down; cancel while dead; a peer adopts (PR) or reaps (devel)
      restart         controller killed; cancel while down; controller restarts and re-adopts its own job
      task-id-window  controller killed and left down; the peer's claim publishes adopt_job_async but
                      pauses before saving the new celery_task_id (adoption.before_task_id_saved); cancel there
      deferred        controller killed and restarted; the first adoption is deferred (adoption.unit_status
                      raises twice); cancel during the deferral, before the next heartbeat re-queues it

    --mode seam (dead, deferred): the kill lands with the owner held before event
    --seam-counter instead of after --lead seconds. dead: the cancel follows the kill directly,
    and the peer's lost check is forced and its heartbeat triggered instead of waiting about two
    minutes for is_lost. deferred: peer claims are vetoed (a slow restart cannot hand the job to
    awx-2, the job-38 class), and the re-queue of the deferred adoption is held before it is
    published (adoption.before_queue, 2nd hit) until the cancel has been issued.
    """
    c0 = containers[0]
    pr = is_pr_branch(c0)
    seam = args.mode == 'seam'
    if seam and args.variant not in ('dead', 'deferred'):
        raise SystemExit('cancel-orphan --mode seam supports --variant dead and deferred')
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    peer_host = container_for_host(peer)
    notes = [f'branch={"PR" if pr else "devel"} variant={args.variant} mode={args.mode}']
    m = {'owner': owner}
    # Recording only (sleep 0): each adoption's snapshot, and each adoption publish.
    arm(peer, 'adoption.after_snapshot', 'sleep', {'job_id': job_id}, seconds=0)
    if seam:
        if args.variant == 'deferred':
            guard_peer(peer, job_id)
            arm(peer, 'adoption.before_queue', 'pause', {'job_id': job_id, 'node': owner}, nth=2, timeout=1800)
            log('seam: the 2nd adoption publish on the owner (the re-queue after the deferral) will hold')
        hold_at_counter(peer, job_id, owner, args.seam_counter)
    else:
        if args.variant == 'deferred':
            arm(peer, 'adoption.before_queue', 'sleep', {'job_id': job_id}, seconds=0)
        time.sleep(args.lead)

    if args.variant == 'task-id-window':
        if not pr:
            raise SystemExit('task-id-window needs the PR branch (_queue_job_adoption)')
        manage(peer, 'failpoint', 'arm', 'adoption.before_task_id_saved', '--action', 'pause', '--match', f'job_id={job_id}', '--timeout', '600')
        log('armed adoption.before_task_id_saved pause')
    if args.variant == 'deferred':
        manage(peer, 'failpoint', 'arm', 'adoption.unit_status', '--action', 'raise', '--match', f'job_id={job_id}', '--times', '2')
        log('armed adoption.unit_status raise (times=2): the first adoption attempt defers')

    t_kill = time.monotonic()
    run(['docker', 'kill', oc])
    m['killed_at'] = utcnow()
    log(f'docker kill {oc}')
    if seam:
        manage(peer, 'failpoint', 'disarm', 'callback.event')
    m['events_at_kill'] = job_state(peer, job_id)['events']

    def do_cancel(why):
        res = cancel_job(peer, job_id)
        log(f'cancel ({why}): {res}')
        m['cancel_at'] = res['at']
        m['cancel_sent_to'] = f"{res['sent_to']['controller_node']}/{res['sent_to']['celery_task_id']}"
        notes.append(
            f"cancel issued at {res['at']} ({why}); addressed to controller_node={res['sent_to']['controller_node']} task={res['sent_to']['celery_task_id']}; log: {res['log']!r}"
        )

    if args.variant in ('dead', 'restart'):
        if not seam:
            time.sleep(5)
        do_cancel(f'{owner} is dead')
    if args.variant == 'dead' and seam:
        arm(peer, 'heartbeat.force_lost', 'trigger', {'node': peer_host, 'other': owner})
        log(f'seam: {peer_host} treats {owner} as lost on its next heartbeat; triggering one now ({trigger_heartbeat(peer)})')
        try:
            wait_hits(peer, 'adoption.after_snapshot', timeout=args.claim_timeout, desc=f'{peer_host} to claim and snapshot the job')
        except TimeoutError as exc:
            notes.append(str(exc))
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost')
    if args.variant == 'restart':
        start_back(oc, owner)
    if args.variant == 'deferred':
        start_back(oc, owner)
        m['restart_s'] = round(time.monotonic() - t_kill, 1)
        if seam:
            hold = wait_hits(peer, 'adoption.before_queue', timeout=600, desc='the re-queue of the deferred adoption to hold')[0]
            m['requeue_held_at'] = hold['at']
            log(f"seam: re-queue held on {hold['node']} at {hold['at']}")
        hits = wait_for(
            'two adoption.unit_status raises',
            lambda: len(json.loads(manage(peer, 'failpoint', 'hits', 'adoption.unit_status', '--fired').stdout)) >= 2 or None,
            300,
            poll=1,
        )
        uh = fired_hits(peer, 'adoption.unit_status')
        m['deferred_at'] = uh[-1]['at']
        log(f'adoption.unit_status fired twice; the adoption deferred ({hits})')
        if not seam:
            time.sleep(2)
        do_cancel('adoption deferred, before the next heartbeat re-queues it')
        if seam:
            manage(peer, 'failpoint', 'disarm', 'adoption.before_queue')
            log('seam: released the re-queue')
    if args.variant == 'task-id-window':
        hit = json.loads(manage(peer, 'failpoint', 'wait', 'adoption.before_task_id_saved', '--timeout', str(args.claim_timeout)).stdout)
        log(f"adoption.before_task_id_saved fired on {hit['node']} at {hit['at']} ctx={hit['ctx']}")
        time.sleep(3)
        do_cancel('claimed, adoption published, celery_task_id not yet updated')
        time.sleep(3)
        manage(peer, 'failpoint', 'release', 'adoption.before_task_id_saved')
        log('released adoption.before_task_id_saved')

    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    notes.append(f"job terminal at about {utcnow()}: status={s['status']} cancel_flag={s['cancel_flag']} controller={s['controller_node']}")
    snaps = fired_hits(peer, 'adoption.after_snapshot')
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in snaps]
    if snaps:
        first = snaps[0] if args.variant == 'dead' else snaps[-1]
        m['adoption_node'] = first['node']
        m['safe_threshold'] = int(first['ctx']['safe_threshold'])
        m['kill_to_adoption_s'] = round(at_seconds(first['at']) - at_seconds(m['killed_at']), 1)
    if args.variant == 'deferred':
        queued = fired_hits(peer, 'adoption.before_queue') if not seam else []
        m['queues'] = [f"{h['node']}@{h['at']}" for h in queued]
        if m.get('cancel_at') and m.get('deferred_at'):
            m['deferral_to_cancel_s'] = round(at_seconds(m['cancel_at']) - at_seconds(m['deferred_at']), 1)
        if m.get('cancel_at') and snaps:
            m['cancel_to_readoption_s'] = round(at_seconds(snaps[-1]['at']) - at_seconds(m['cancel_at']), 1)
        if s['controller_node'] != owner:
            m['invalid'] = f"a peer took the job ({s['controller_node']}) instead of the restarted owner"
    if args.variant == 'dead' and not snaps:
        m['invalid'] = 'no adoption (reaped or never claimed)'
    # Whatever the job row says, did the work itself stop?
    watch(
        peer,
        job_id,
        unit,
        420,
        until=lambda _s: unit_status(unit).get('StateName') in ('Succeeded', 'Failed', 'Canceled') or 'error' in unit_status(unit),
        poll=15,
        label='after terminal',
    )
    m['unit_end'] = unit_status(unit)
    notes.append(f"exec-node unit after the job ended: {m['unit_end']}; playbook processes: {exec_node_processes(r'ansible-playbook')}")
    log(notes[-1])
    if args.variant in ('dead', 'task-id-window'):
        start_back(oc, owner)
    manage(peer, 'failpoint', 'disarm', '--all')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes, metrics=m)


# --- capacity ------------------------------------------------------------------------------


def scenario_capacity_strand(containers, args):
    """Capacity (a): an orphan that no node has room for, observed for --observe seconds.

    Needs awx-2's cpu capacity forced to 1 (SYSTEM_TASK_ABS_CPU=0.25 for awx-2 only in
    local_settings.py), so that capacity_adjustment=0 gives it capacity 1 and 1.0 gives 616.
    1. Disable awx-1 so the task manager puts two long filler jobs on awx-2 as controller.
    2. Re-enable awx-1 and launch the scenario job (controlled by awx-1).
    3. Set awx-2 capacity_adjustment=0: capacity 1, consumed 2, remaining -1. Neither the
       lost-instance path (needs remaining >= 1) nor the sweep (needs remaining >= 0) may claim.
    4. Kill awx-1 for good. Watch the orphan and a second launch of the same template.
    5. Restore awx-2's capacity and watch what happens to the orphan.
    """
    c0 = 'tools_awx_2'
    pr = is_pr_branch(c0)
    since = since_now()
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    notes = [f'branch={"PR" if pr else "devel"}']
    log(f"awx-2 cpu_capacity check: {instances(c0)['awx-2']}")
    set_instance(c0, 'awx-1', enabled=False)
    log('awx-1 disabled: the task manager places the fillers on awx-2')
    filler_jt = setup(containers, 'failpoint filler', 'quiet.yml', {'quiet_seconds': args.observe + 900}, allow_simultaneous=True)
    fillers = [launch(c0, filler_jt) for _ in range(2)]
    for f in fillers:
        fs = wait_for(f'filler {f} running', lambda f=f: (s := job_state(c0, f))['status'] == 'running' and s['work_unit_id'] and s, 300)
        log(f"filler {f}: controller={fs['controller_node']} execution={fs['execution_node']}")
        notes.append(f"filler job {f}: controller={fs['controller_node']}")
    set_instance(c0, 'awx-1', enabled=True)
    wait_for('awx-1 capacity back', lambda: instances(c0)['awx-1']['capacity'] > 0, 180, poll=5)
    log(f"awx-1 re-enabled: {instances(c0)['awx-1']}")
    job_id, st = start_job(containers, args, reset=False)
    owner, unit = st['controller_node'], st['work_unit_id']
    if owner != 'awx-1':
        raise SystemExit(f'scenario job went to {owner}, expected awx-1')
    set_instance(c0, 'awx-2', capacity_adjustment=0)
    inst = wait_for('awx-2 capacity 1', lambda: (i := instances(c0))['awx-2']['capacity'] == 1 and i, 180, poll=5)
    log(f"awx-2 capacity now {inst['awx-2']['capacity']} (2 fillers controlled): {inst['awx-2']}")
    time.sleep(args.lead)
    run(['docker', 'kill', 'tools_awx_1'])
    log('docker kill tools_awx_1 (left down)')
    killed_at = time.monotonic()

    second = None

    def extra():
        nonlocal second
        if second is None and time.monotonic() - killed_at > 200:
            jt = orm(c0, f'from awx.main.models import UnifiedJob\nemit(UnifiedJob.objects.get(pk={job_id}).unified_job_template_id)\n')
            second = launch(c0, jt)
            log(f'launched a second job {second} from the same template (allow_simultaneous=False)')
            notes.append(f'second launch of the same template: job {second} at {utcnow()}')
        out = {'awx-1': instances(c0)['awx-1']['state']}
        if second:
            s2 = job_state(c0, second)
            out['second'] = (s2['status'], s2['controller_node'], s2['job_explanation'])
        return out

    s = watch(c0, job_id, unit, args.observe, until=terminal, poll=15, extra=extra)
    notes.append(
        f"after {args.observe}s with awx-1 dead and awx-2 full: status={s['status']} controller={s['controller_node']} "
        f"last_event_age={s['last_event_age']}s unit={unit_status(unit)}"
    )
    log(notes[-1])
    if second:
        s2 = job_state(c0, second)
        notes.append(f"second job {second}: status={s2['status']} explanation={s2['job_explanation']!r}")
        log(notes[-1])

    set_instance(c0, 'awx-2', capacity_adjustment=1)
    log('restored awx-2 capacity_adjustment=1')
    s = watch(c0, job_id, unit, args.finish_timeout, until=terminal, poll=10, label='after restore')
    notes.append(f"after restoring capacity: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    for f in fillers + ([second] if second else []):
        orm(
            c0,
            f'from awx.main.models import UnifiedJob\nj = UnifiedJob.objects.get(pk={f})\nemit(j.cancel() if j.status in ("pending", "waiting", "running") else j.status)\n',
        )
    log(f'canceled fillers {fillers} and second job {second}')
    start_back('tools_awx_1', 'awx-1')
    time.sleep(args.settle)
    for f in fillers + ([second] if second else []):
        fs = job_state(c0, f)
        notes.append(f"job {f} final: status={fs['status']} controller={fs['controller_node']}")
    return report(containers, job_id, since, args, unit, notes)


def scenario_capacity_disabled(containers, args):
    """Capacity (b): a disabled controller (capacity 0) adopts without limit.

    1. Disable awx-2 (enabled=False; its next health check sets capacity 0) and launch
       --count jobs; the task manager can only place them on awx-1.
    2. Kill awx-1 for good. awx-2 is READY but disabled: the task manager will not give it
       work, but _adoption_slot_available() treats capacity 0 as "fail open".
    3. Launch one more job to show the task manager's view, then watch all of them.
    """
    c0 = 'tools_awx_2'
    pr = is_pr_branch(c0)
    since = since_now()
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    notes = [f'branch={"PR" if pr else "devel"}']
    set_instance(c0, 'awx-2', enabled=False)
    wait_for('awx-2 capacity 0', lambda: instances(c0)['awx-2']['capacity'] == 0, 180, poll=5)
    log(f"awx-2 disabled: {instances(c0)['awx-2']}")
    jt = setup(containers, 'failpoint chatty multi', 'chatty.yml', {'iterations': args.iterations}, allow_simultaneous=True)
    jobs = [launch(c0, jt) for _ in range(args.count)]
    units = {}
    for j in jobs:
        js = wait_for(f'job {j} running', lambda j=j: (s := job_state(c0, j))['status'] == 'running' and s['work_unit_id'] and s, 300)
        units[j] = js['work_unit_id']
        log(f"job {j}: controller={js['controller_node']} execution={js['execution_node']} unit={js['work_unit_id']}")
    time.sleep(args.lead)
    run(['docker', 'kill', 'tools_awx_1'])
    log('docker kill tools_awx_1 (left down)')
    extra_job = launch(c0, jt)
    log(f'launched job {extra_job} after the kill (task manager view)')

    def states():
        return {j: (lambda s: (s['status'], s['controller_node']))(job_state(c0, j)) for j in jobs + [extra_job]}

    last = None
    end = time.monotonic() + args.finish_timeout
    while time.monotonic() < end:
        cur = states()
        inst = instances(c0)['awx-2']
        snap = (json.dumps(cur), inst['capacity'], inst['enabled'])
        if snap != last:
            log(f"jobs: {cur}; awx-2 enabled={inst['enabled']} capacity={inst['capacity']}")
            last = snap
        if all(cur[j][0] not in ('pending', 'waiting', 'running') for j in jobs):
            break
        time.sleep(10)
    notes.append(f'final states: {states()}')
    set_instance(c0, 'awx-2', enabled=True)
    log('re-enabled awx-2')
    orm(
        c0,
        f'from awx.main.models import UnifiedJob\nj = UnifiedJob.objects.get(pk={extra_job})\nemit(j.cancel() if j.status in ("pending", "waiting", "running") else j.status)\n',
    )
    start_back('tools_awx_1', 'awx-1')
    time.sleep(args.settle)
    results = []
    for j in jobs:
        r = report(containers, j, since, args, units[j], notes if j == jobs[-1] else ())
        results.append(r)
    return {'ok': all(r['ok'] for r in results)}


# --- resume hybrid -------------------------------------------------------------------------

HYBRID_IG = 'failpoint-hybrid-awx-1'


def hybrid_setup(containers):
    """Make awx-1 and awx-2 hybrid, give awx-1 the EE image, and an instance group of awx-1 only."""
    have = run(['docker', 'exec', 'tools_awx_1', 'podman', 'images', '--format', '{{.Repository}}:{{.Tag}}'], check=False).stdout
    if 'quay.io/ansible/awx-ee:latest' not in have:
        log('copying quay.io/ansible/awx-ee:latest from receptor-1 into awx-1 podman storage')
        subprocess.run(
            'docker exec tools_receptor_1 podman save quay.io/ansible/awx-ee:latest | docker exec -i tools_awx_1 podman load',
            shell=True,
            check=True,
            capture_output=True,
        )
    for h in ('awx-1', 'awx-2'):
        set_instance(containers[0], h, node_type='hybrid')
    out = orm(
        containers[0],
        f'''
from awx.main.models import Instance, InstanceGroup
ig, _ = InstanceGroup.objects.get_or_create(name={HYBRID_IG!r})
ig.policy_instance_percentage = 0
ig.policy_instance_minimum = 0
ig.policy_instance_list = ['awx-1']
ig.save()
ig.instances.set([Instance.objects.get(hostname='awx-1')])
emit({{i.hostname: (i.node_type, [g.name for g in i.rampart_groups.all()]) for i in Instance.objects.all()}})
''',
    )
    log(f'hybrid setup: {out}')


def hybrid_teardown(containers):
    for c in containers:
        if manage(c, 'failpoint', 'list', check=False).returncode == 0:
            break
    for h in ('awx-1', 'awx-2'):
        set_instance(c, h, node_type='control')
    out = orm(
        c,
        f'''
from awx.main.models import Instance, InstanceGroup, JobTemplate
JobTemplate.objects.filter(name='failpoint hybrid').first() and JobTemplate.objects.get(name='failpoint hybrid').instance_groups.clear()
InstanceGroup.objects.filter(name={HYBRID_IG!r}).delete()
from awx.main.tasks.system import apply_cluster_membership_policies
apply_cluster_membership_policies()
emit({{i.hostname: (i.node_type, [g.name for g in i.rampart_groups.all()]) for i in Instance.objects.all()}})
''',
    )
    log(f'hybrid teardown: {out}')


def scenario_hybrid_resume(containers, args):
    """Resume hybrid: a job controlled and executed by hybrid awx-1 when awx-1 goes not-READY.

    --trigger kill        docker kill awx-1 and leave it down (the lost-instance path decides)
    --trigger stop        docker stop awx-1 (graceful: announce_shutdown, then the EE dies with the node)
    --trigger redis-blip  awx-1 fails one Redis ping (health_check.redis_ping), so it is UNAVAILABLE
                          for one heartbeat while its EE keeps running
    Run with --hybrid-setup once before and --hybrid-teardown after (or both on one run).
    """
    c0 = 'tools_awx_2'
    pr = is_pr_branch(c0)
    if args.hybrid_setup:
        hybrid_setup(containers)
    since = since_now()
    job_id, st = start_job(containers, args, jt_name='failpoint hybrid', instance_group=HYBRID_IG, allow_local=True)
    owner, unit = st['controller_node'], st['work_unit_id']
    notes = [f"branch={'PR' if pr else 'devel'} trigger={args.trigger}; controller={owner} execution={st['execution_node']}"]
    if not (owner == st['execution_node'] == 'awx-1'):
        raise SystemExit(f'expected awx-1 to control and execute the job, got {st}')
    time.sleep(args.lead)
    procs = lambda: run(['docker', 'exec', 'tools_awx_1', 'pgrep', '-fc', 'ansible-playbook'], check=False).stdout.strip()  # noqa: E731
    log(f'ansible-playbook processes on awx-1: {procs()}')

    if args.trigger == 'kill':
        run(['docker', 'kill', 'tools_awx_1'])
        log('docker kill tools_awx_1 (left down)')
    elif args.trigger == 'stop':
        run(['docker', 'stop', '-t', '60', 'tools_awx_1'])
        log('docker stop -t 60 tools_awx_1 returned (left down)')
    else:
        manage(
            c0,
            'failpoint',
            'arm',
            'health_check.redis_ping',
            '--action',
            'raise',
            '--exception',
            'redis.exceptions.ConnectionError',
            '--match',
            'node=awx-1',
            '--times',
            '1',
        )
        log('armed health_check.redis_ping on awx-1 (times=1)')

    def extra():
        i = instances(c0)
        return {'awx-1': (i['awx-1']['state'], i['awx-1']['capacity']), 'playbooks_on_awx_1': procs() if args.trigger == 'redis-blip' else 'n/a'}

    try:
        s = watch(c0, job_id, None, args.finish_timeout, until=terminal, poll=5, extra=extra)
        notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    finally:
        manage(c0, 'failpoint', 'disarm', '--all')
        if args.trigger != 'redis-blip':
            start_back('tools_awx_1', 'awx-1')
    time.sleep(args.settle)
    result = report(containers, job_id, since, args, unit, notes)
    if args.hybrid_teardown:
        hybrid_teardown(containers)
    return result


# --- event queue ---------------------------------------------------------------------------


def scenario_event_queue(containers, args):
    """Event queue: events still queued for the callback receiver when the controller restarts.

    1. Launch a chatty job; after --lead seconds pause every callback receiver flush on its
       controller C (callback_receiver.before_flush), so new events pile up in Redis and in the
       workers' buffers instead of reaching the DB.
    2. Restart C: --trigger kill (docker kill + start; Redis is a separate container and keeps
       its list) or --trigger dispatcher (supervisorctl restart of the dispatcher only; on the PR
       awx-2's sweep is disabled with sweep.before_claim raise so the adoption stays on C).
    3. C's adoption snapshots the DB (which lacks the queued events) and replays from byte 0.
    4. Release the flush; count duplicate counters.

    --mode seam (trigger kill): the backlog is counted in events, not seconds. C's job task is
    held before event --seam-counter until the receiver has stored everything before it; then
    every receiver worker on C is held before its next Redis pop (callback_receiver.before_read,
    so no event sits in a worker buffer that dies with the kill), and the hold on the job task
    moves to counter + --seam-backlog. Exactly --seam-backlog events are in Redis at the kill.
    Peer claims are vetoed so a slow restart cannot hand the job to awx-2.
    """
    c0 = containers[0]
    pr = is_pr_branch(c0)
    seam = args.mode == 'seam'
    if seam and args.trigger != 'kill':
        raise SystemExit('event-queue --mode seam supports --trigger kill only')
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    notes = [f"branch={'PR' if pr else 'devel'} trigger={args.trigger} mode={args.mode}"]
    m = {'owner': owner}
    # Armed only to record the snapshot: an unarmed failpoint leaves no hit to wait on.
    manage(peer, 'failpoint', 'arm', 'adoption.after_snapshot', '--action', 'sleep', '--seconds', '0', '--match', f'job_id={job_id}')
    if seam:
        n, b = args.seam_counter, args.seam_backlog
        guard_peer(peer, job_id)
        hold_at_counter(peer, job_id, owner, n)
        wait_db_events(peer, job_id, n)
        arm(peer, 'callback_receiver.before_read', 'pause', {'node': owner}, timeout=1800)
        workers = setting(oc, 'JOB_EVENT_WORKERS')
        wait_hits(peer, 'callback_receiver.before_read', count=workers, timeout=60, desc=f'{workers} receiver workers on {owner} to hold')
        log(f'seam: all {workers} receiver workers on {owner} hold before their next Redis pop')
        arm(peer, 'callback.event', 'pause', {'job_id': job_id, 'node': owner, 'counter': n + b}, timeout=1800)
        wait_hits(peer, 'callback.event', lambda h: str(h['ctx'].get('counter')) == str(n + b), timeout=300)
        log(f'seam: {owner} let events {n}..{n + b - 1} through and holds before {n + b}')
    else:
        time.sleep(args.lead)
        manage(peer, 'failpoint', 'arm', 'callback_receiver.before_flush', '--action', 'pause', '--match', f'node={owner}', '--timeout', '1200')
        log(f'armed callback_receiver.before_flush pause on {owner}')
        manage(peer, 'failpoint', 'wait', 'callback_receiver.before_flush', '--timeout', '60')
        time.sleep(args.backlog)
    s = job_state(peer, job_id)
    m['db_events_at_kill'] = s['events']
    m['redis_backlog_at_kill'] = redis_backlog(oc)
    notes.append(f"before restart: {s['events']} events in DB, Redis backlog on {owner}: {m['redis_backlog_at_kill']}")
    log(notes[-1])
    if args.trigger == 'kill':
        t_kill = time.monotonic()
        run(['docker', 'kill', oc])
        m['killed_at'] = utcnow()
        log(f'docker kill {oc}')
        if seam:
            # The held job task died with the node; the restarted node's replay must not stop.
            manage(peer, 'failpoint', 'disarm', 'callback.event')
        run(['docker', 'start', oc])
        log(f'docker start {oc}')
        wait_for(f'{owner} to answer awx-manage', lambda: manage(oc, 'failpoint', 'list', check=False).returncode == 0, 600, poll=10)
        m['restart_s'] = round(time.monotonic() - t_kill, 1)
        log(f'{owner} is back (awx-manage answers) after {m["restart_s"]}s')
    else:
        if pr:
            manage(peer, 'failpoint', 'arm', 'sweep.before_claim', '--action', 'raise', '--match', f'node={container_for_host(peer)}')
            log('armed sweep.before_claim raise on the peer: it must not steal the job')
        run(['docker', 'exec', oc, 'supervisorctl', 'restart', 'tower-processes:awx-dispatcher'])
        log(f'restarted the dispatcher on {owner}')
    hit = json.loads(manage(peer, 'failpoint', 'wait', 'adoption.after_snapshot', '--timeout', str(args.finish_timeout)).stdout)
    log(f"adoption snapshot on {hit['node']} at {hit['at']}: {hit['ctx']}")
    notes.append(f"adoption snapshot at {hit['at']} on {hit['node']}: {hit['ctx']}")
    m['snapshot_node'] = hit['node']
    m['kill_to_snapshot_s'] = round(at_seconds(hit['at']) - at_seconds(m['killed_at']), 1) if 'killed_at' in m else None
    m['safe_threshold'] = int(hit['ctx']['safe_threshold'])
    if hit['node'] != owner:
        m['invalid'] = f"adopted by {hit['node']}, not the restarted owner"
    if not seam:
        time.sleep(10)
    m['redis_backlog_at_release'] = redis_backlog(oc)
    notes.append(f"at release: {job_state(peer, job_id)['events']} events in DB, Redis backlog: {m['redis_backlog_at_release']}")
    log(notes[-1])
    release = 'callback_receiver.before_read' if seam else 'callback_receiver.before_flush'
    if not seam:
        manage(peer, 'failpoint', 'release', release)
        time.sleep(2)
    # Disarming releases every held worker too; a released-but-armed before_read would
    # record a hit for every Redis pop.
    manage(peer, 'failpoint', 'disarm', release)
    log(f'released and disarmed {release}')
    wait_finished(peer, job_id, args.finish_timeout)
    manage(peer, 'failpoint', 'disarm', '--all')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes, metrics=m)


def container_for_host(container):
    return container.replace('tools_', '').replace('_', '-')


# --- host map ------------------------------------------------------------------------------

HOSTMAP_INV = 'failpoint hosts'
HOSTMAP_HOSTS = [f'fp-h{i}' for i in range(1, 6)]


def hostmap_inventory(container):
    """(Re)create the 5-host inventory; return {name: id}."""
    return orm(
        container,
        f'''
from awx.main.models import Inventory, Organization, Host
org = Organization.objects.get(name='Default')
inv, _ = Inventory.objects.get_or_create(name={HOSTMAP_INV!r}, organization=org)
inv.hosts.all().delete()
for n in {HOSTMAP_HOSTS!r}:
    Host.objects.create(name=n, inventory=inv, variables='ansible_connection: local', enabled=True)
emit({{h.name: h.id for h in inv.hosts.all()}})
''',
    )


def hostmap_mutate(container):
    """fp-h2 deleted, fp-h3 deleted and recreated (new id), fp-h4 disabled; fp-h1, fp-h5 untouched."""
    return orm(
        container,
        f'''
from django.utils.timezone import now
from awx.main.models import Inventory, Host
inv = Inventory.objects.get(name={HOSTMAP_INV!r})
at = now()
inv.hosts.get(name='fp-h2').delete()
inv.hosts.get(name='fp-h3').delete()
Host.objects.create(name='fp-h3', inventory=inv, variables='ansible_connection: local', enabled=True)
h4 = inv.hosts.get(name='fp-h4'); h4.enabled = False; h4.save()
emit(dict(at=at, hosts={{h.name: (h.id, h.enabled) for h in inv.hosts.all()}}))
''',
    )


def hostmap_analysis(container, job_id, original, threshold):
    return orm(
        container,
        f'''
from django.db.models import Count, Min, Max
from awx.main.models import Job
j = Job.objects.get(pk={job_id})
qs = j.get_event_queryset().exclude(host_name='')
thr = {threshold!r}
rows = []
for r in qs.values('host_name', 'host_id').annotate(n=Count('id'), lo=Min('counter'), hi=Max('counter')).order_by('host_name', 'host_id'):
    rows.append(r)
replayed = []
if thr is not None:
    for r in qs.filter(counter__gt=thr).values('host_name', 'host_id').annotate(n=Count('id')).order_by('host_name', 'host_id'):
        replayed.append(r)
summ = list(j.job_host_summaries.values('host_name', 'host_id', 'ok', 'failures', 'dark').order_by('host_name'))
emit(dict(original={original!r}, threshold=thr, events_by_host=rows, events_above_threshold=replayed, summaries=summ))
''',
    )


def scenario_host_map(containers, args):
    """Host map: inventory changes while a job is orphaned; adoption rebuilds host_map from the current inventory.

    1. A 5-host inventory (ansible_connection=local); chatty.yml over all five.
    2. --adopt-via restart: docker kill the controller, mutate the inventory while it is down,
       start it again (same-node adoption). --adopt-via peer (PR): kill and leave it down;
       mutate before the peer claims (cross-node). --adopt-via none: mutate mid-job with no
       failover (the normal path's baseline).
    3. Compare JobEvent.host_id and JobHostSummary.host_id with the ids the job started with.
    """
    c0 = containers[0]
    pr = is_pr_branch(c0)
    original = hostmap_inventory(c0)
    log(f'inventory {HOSTMAP_INV!r}: {original}')
    since = since_now()
    job_id, st = start_job(containers, args, jt_name='failpoint hostmap', inventory=HOSTMAP_INV)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    notes = [f"branch={'PR' if pr else 'devel'} adopt_via={args.adopt_via}; original host ids {original}"]
    manage(peer, 'failpoint', 'arm', 'adoption.after_snapshot', '--action', 'sleep', '--seconds', '0', '--match', f'job_id={job_id}')
    time.sleep(args.lead)
    if args.adopt_via == 'none':
        m = hostmap_mutate(peer)
        log(f'mutated inventory mid-job (no failover): {m}')
        notes.append(f"inventory mutated at {m['at']}: {m['hosts']}")
    else:
        run(['docker', 'kill', oc])
        log(f'docker kill {oc}')
        m = hostmap_mutate(peer)
        log(f'mutated inventory while {owner} is down: {m}')
        notes.append(f"inventory mutated at {m['at']}: {m['hosts']}")
        if args.adopt_via == 'restart':
            start_back(oc, owner)
        else:
            s = wait_for('a peer to claim the job', lambda: (s := job_state(peer, job_id))['controller_node'] != owner and s, args.claim_timeout)
            log(f"job {job_id} claimed by {s['controller_node']}")
    wait_finished(peer, job_id, args.finish_timeout)
    if args.adopt_via == 'peer':
        start_back(oc, owner)
    time.sleep(args.settle)
    snaps = json.loads(manage(peer, 'failpoint', 'hits', 'adoption.after_snapshot', '--fired').stdout)
    manage(peer, 'failpoint', 'disarm', '--all')
    thr = min((int(h['ctx']['safe_threshold']) for h in snaps), default=None)
    a = hostmap_analysis(peer, job_id, original, thr)
    print('\n=== Host map analysis ===')
    print(f"  original ids: {a['original']}; adoption safe_threshold={a['threshold']}")
    print('  events by (host_name, host_id): ')
    for r in a['events_by_host']:
        tag = 'original' if original.get(r['host_name']) == r['host_id'] else 'NOT ORIGINAL'
        print(f"    {r['host_name']:<6} host_id={r['host_id']!s:<6} n={r['n']:<4} counters {r['lo']}-{r['hi']}  {tag}")
    print('  events above the snapshot threshold (replayed by adoption):')
    for r in a['events_above_threshold']:
        tag = 'original' if original.get(r['host_name']) == r['host_id'] else 'NOT ORIGINAL'
        print(f"    {r['host_name']:<6} host_id={r['host_id']!s:<6} n={r['n']:<4} {tag}")
    print('  job host summaries:')
    for r in a['summaries']:
        tag = 'original' if original.get(r['host_name']) == r['host_id'] else 'NOT ORIGINAL'
        print(f"    {r['host_name']:<6} host_id={r['host_id']!s:<6} ok={r['ok']} failures={r['failures']} dark={r['dark']}  {tag}")
    notes.append(f'host map analysis: {json.dumps(a, default=str)}')
    result = report(containers, job_id, since, args, unit, notes)
    if args.out:
        with open(os.path.join(args.out, f'{run_label(args)}-job{job_id}', 'hostmap.json'), 'w') as fh:
            json.dump(a, fh, indent=2, default=str)
    return result


# --- log rotation (container groups) -------------------------------------------------------

CG_NAME = 'failpoint-minikube'
CG_POD_SPEC = """apiVersion: v1
kind: Pod
metadata:
  namespace: default
spec:
  containers:
    - image: 'quay.io/ansible/awx-ee:latest'
      imagePullPolicy: IfNotPresent
      name: worker
      args:
        - ansible-runner
        - worker
        - '--private-data-dir=/runner'"""


def cg_setup(container, token_file, host):
    with open(token_file) as fh:
        token = fh.read().strip()
    return orm(
        container,
        f'''
from awx.main.models import Credential, CredentialType, InstanceGroup, Organization
ct = CredentialType.objects.get(name='OpenShift or Kubernetes API Bearer Token')
cred, _ = Credential.objects.get_or_create(name={CG_NAME!r}, defaults=dict(credential_type=ct, organization=Organization.objects.get(name='Default')))
cred.inputs = {{'host': {host!r}, 'verify_ssl': False, 'bearer_token': {token!r}}}
cred.save()
ig, _ = InstanceGroup.objects.get_or_create(name={CG_NAME!r}, defaults=dict(is_container_group=True))
ig.is_container_group = True
ig.credential = cred
ig.pod_spec_override = {CG_POD_SPEC!r}
ig.save()
emit(dict(ig=ig.id, cred=cred.id))
''',
    )


def kube(args, kubeconfig):
    return run(['kubectl', '--kubeconfig', kubeconfig, *args], check=False).stdout


def scenario_log_rotation(containers, args):
    """Log rotation: a container-group job orphaned while kubelet rotates its pod log.

    Needs a Kubernetes cluster reachable from the control nodes as --k8s-host, kubelet
    containerLogMaxSize small (e.g. 128Ki), and --kubeconfig/--token-file for it.
    1. Launch chatty.yml in a container group; note the job pod.
    2. After --lead seconds kill the controller and leave it down (PR: the peer adopts through
       adopt_container_group_job; devel: the lost-instance path reaps).
    3. Record the pod log size kubelet still serves vs. the bytes written, wait for the job.
    4. Count stored event counters against the playbook's known event count (iterations + 7).
    """
    c0 = 'tools_awx_2'
    pr = is_pr_branch(c0)
    ids = cg_setup(c0, args.token_file, args.k8s_host)
    log(f'container group setup: {ids}')
    since = since_now()
    job_id, st = start_job(containers, args, jt_name='failpoint cg', instance_group=CG_NAME, allow_local=True)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    notes = [f"branch={'PR' if pr else 'devel'}; controller={owner} execution={st['execution_node']!r}; expected events {args.iterations + 7}"]

    def pod_info():
        name = kube(
            ['get', 'pods', '-l', f'ansible-awx-job-id={job_id}', '-o', 'jsonpath={.items[0].metadata.name} {.items[0].status.phase}'], args.kubeconfig
        ).strip()
        served = len(kube(['logs', name.split()[0]], args.kubeconfig)) if name else 0
        files = run(
            [
                'bash',
                '-c',
                f'MINIKUBE_HOME={args.minikube_home} {args.minikube} ssh -- \'sudo sh -c "ls -l /var/log/pods/default_{name.split()[0]}_*/worker/"\'',
            ],
            check=False,
        ).stdout.strip()
        return {'pod': name, 'served_log_bytes': served, 'files': ' | '.join(line.split(None, 4)[-1] for line in files.splitlines()[1:])}

    if args.delay_adoption:
        # Holds the adopter between its claim and the pod triage, so the pod can finish (and
        # kubelet rotate its log further) while the job is orphaned.
        manage(c0, 'failpoint', 'arm', 'adoption.after_claim', '--action', 'sleep', '--seconds', str(args.delay_adoption), '--match', f'job_id={job_id}')
        log(f'armed adoption.after_claim sleep {args.delay_adoption}s')
    time.sleep(args.lead)
    log(f'pod before the kill: {pod_info()}')
    run(['docker', 'kill', oc])
    log(f'docker kill {oc} (left down)')
    s = watch(c0, job_id, None, args.finish_timeout, until=terminal, poll=10, extra=pod_info)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}; pod {pod_info()}")
    start_back(oc, owner)
    time.sleep(args.settle)
    counters = orm(
        c0,
        f'''
from django.db.models import Min, Max, Count
from awx.main.models import Job
qs = Job.objects.get(pk={job_id}).get_event_queryset()
cs = sorted(set(qs.values_list('counter', flat=True)))
gaps = []
prev = 0
for c in cs:
    if c != prev + 1:
        gaps.append((prev + 1, c - 1))
    prev = c
emit(dict(stored=qs.count(), distinct=len(cs), lo=cs[0] if cs else None, hi=cs[-1] if cs else None, gaps=gaps[:20],
          stats=qs.filter(event='playbook_on_stats').count()))
''',
    )
    notes.append(f'event counters: {counters} (expected 1..{args.iterations + 7})')
    log(notes[-1])
    return report(containers, job_id, since, args, unit, notes)


# --- Part 3: adopter dies, claim race, workflow orphan, many orphans ---------------------


def registry(container):
    """Failpoint names this branch registers (the PR has more than devel)."""
    return set(re.findall(r'^(\S+)$', manage(container, 'failpoint', 'registry').stdout, re.M))


def all_hits(container, name):
    """Every recorded hit of name, fired or not (includes 'resumed' records)."""
    return json.loads(manage(container, 'failpoint', 'hits', name).stdout)


def pause_hits(container, name):
    return [h for h in fired_hits(container, name) if h['action'] == 'pause']


def by_node(hits):
    return dict(Counter(h['node'] for h in hits))


def parallel(*fns):
    """Run the callables at the same time (each is a docker exec round trip); return their results."""
    results = [None] * len(fns)

    def runner(i, fn):
        results[i] = fn()

    threads = [threading.Thread(target=runner, args=(i, fn)) for i, fn in enumerate(fns)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def release_together(container, names, lead=2.0):
    """One UPDATE releases every name; every holder resumes at the same scheduled instant."""
    out = manage(container, 'failpoint', 'release', *names, '--in', str(lead)).stdout
    res = json.loads(out[out.index('{') :])
    res['at_utc'] = datetime.fromtimestamp(res['at'], timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    log(f"released {', '.join(names)} together: scheduled for {res['at_utc']} ({res['rows']} rows)")
    return res


def resumed(container, names):
    """The 'resumed' records of held callers: node, pid, lateness, wake time."""
    rows = []
    for name in names:
        for h in all_hits(container, name):
            if h['action'] == 'resumed':
                rows.append({'name': name, 'node': h['node'], 'pid': h['pid'], 'late_ms': h['ctx'].get('late_ms'), 'woke': h['ctx'].get('woke')})
    return rows


def arm_recorders(container, job_id, names):
    """Arm no-op recorders (sleep 0) for the names this branch has, in one awx-manage shell
    (one docker exec per arm costs about 3 s, enough for a job to run past a hold point)."""
    match = {'job_id': str(job_id)} if job_id else {}
    done = orm(
        container,
        f'''
from awx.main.utils import failpoints
done = []
for name in {list(names)!r}:
    if name in failpoints.REGISTRY:
        failpoints.arm(name, 'sleep', match={match!r}, seconds=0)
        done.append(name)
emit(done)
''',
    )
    log(f'recorders armed: {", ".join(done)}')
    return done


def arm_hold(container, job_id, owner, counter):
    """Seam, first half of hold_at_counter: arm the hold as soon as the job runs."""
    arm(container, 'callback.event', 'pause', {'job_id': job_id, 'node': owner, 'counter': counter}, timeout=1800)


def wait_hold(container, job_id, owner, counter):
    hit = wait_hits(container, 'callback.event', lambda h: h['node'] == owner and str(h['ctx'].get('counter')) == str(counter), timeout=600)[0]
    log(f'seam: {owner} holds job {job_id} before event counter {counter} (at {hit["at"]})')
    return hit


def force_lost(container, node, other):
    """Seam: `node` treats `other` as lost on its next heartbeat, and one is triggered now."""
    arm(container, 'heartbeat.force_lost', 'trigger', {'node': node, 'other': other})
    log(f'seam: {node} treats {other} as lost; triggering its heartbeat now ({trigger_heartbeat(container_for(node))})')


def kill(container):
    run(['docker', 'kill', container])
    at = utcnow()
    log(f'docker kill {container} (left down)')
    return at


# Log lines that say what each claimant decided. {j} is the job id.
CLAIM_PATTERNS = {
    'lost_claimed': r'Cross-controller adoption queued for job {j}\b',
    'lost_already_claimed': r'Cross-controller adoption skipped for job {j}: already claimed',
    'lost_deferred_capacity': r'Cross-controller adoption deferred for job {j}\b',
    'sweep_claimed': r'Orphan sweep adopting job {j}:',
    'sweep_failed': r'Orphan sweep failed to adopt job {j}\b',
    'task_claim_skipped': r'Adoption skipped for job {j}\b',
    'adopting': r'Adopting job {j}\b',
    'finalized_via_adoption': r'Job {j} finalized via adoption',
    'lock_busy': r'task_manager_lock held, deferring offline handling',
    'release_errors': r'Error releasing work unit|Could not confirm release of receptor work unit|While releasing work',
}


def count_log_lines(logs, job_id, unit_id=None):
    """Per pattern, per node: how many log lines match (a message is logged once per node)."""
    out = {}
    for key, pat in CLAIM_PATTERNS.items():
        rx = re.compile(pat.format(j=job_id))
        per = {}
        for c, lines in logs.items():
            n = sum(1 for line in lines if rx.search(line) and (key != 'release_errors' or not unit_id or unit_id in line))
            if n:
                per[container_for_host(c)] = n
        out[key] = per
    return out


def scenario_claim_race(containers, args):
    """Claim race: two live controllers try to claim the same orphan at the same instant.

    Needs 3 control nodes and the PR branch (devel never claims across nodes). The job's
    controller O is held before event --seam-counter and killed; the other two (A < B) race:
      sweep-sweep  O is first marked offline by A's lost path with its claim vetoed
                   (lost_instance.before_claim raise); then A's and B's orphan sweeps are both
                   held at sweep.before_claim and released at one instant.
      lost-sweep   as above, then A is held at lost_instance.before_claim (A holds
                   task_manager_lock) and B at sweep.before_claim; released at one instant.
      lost-lost    both lost paths are forced at once with lost_instance.before_claim held:
                   shows that task_manager_lock admits only one of them.
      lost-then-sweep  no race: A's lost path is held, A's next heartbeat sweeps and claims,
                   then the lost path resumes on the same node (forces the interleaving in
                   which the job ends up carrying a discarded duplicate's task id).
    --cancel-in-adoption cancels once the winner streams and records whether the cancel is
    addressed to the adoption task that is actually running.
    Only A is told O is lost (heartbeat.force_lost on A), so B's own lost path cannot run before
    O's natural is_lost (120 s). Recorders count claims (adoption.before_queue), adoption tasks
    (adoption.after_claim) and streams (adoption.after_snapshot) per node.
    """
    if len(containers) < 3:
        raise SystemExit('claim-race needs three control nodes')
    c0 = containers[0]
    if 'sweep.before_claim' not in registry(c0):
        raise SystemExit('claim-race needs the PR branch: devel has no cross-controller claim to race')
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    a, b = sorted(container_for_host(c) for c in containers if c != oc)
    ca, cb = container_for(a), container_for(b)
    m = {'owner': owner, 'racer_a': a, 'racer_b': b, 'variant': args.variant}
    notes = [f'claim-race {args.variant}: owner {owner}, racers {a} and {b}']
    arm_hold(ca, job_id, owner, args.seam_counter)
    arm_recorders(
        ca,
        job_id,
        [
            'adoption.before_queue',
            'adoption.after_claim',
            'adoption.after_snapshot',
            'job.after_finalize_before_release',
            'adoption.after_finalize_before_release',
        ],
    )
    if args.variant == 'lost-lost':
        arm(ca, 'lost_instance.before_claim', 'pause', {'job_id': job_id}, timeout=900)
    else:
        arm(ca, 'lost_instance.before_claim', 'raise', {'job_id': job_id})
    arm(ca, 'sweep.before_claim', 'raise', {'job_id': job_id})
    wait_hold(ca, job_id, owner, args.seam_counter)
    m['killed_at'] = kill(oc)
    manage(ca, 'failpoint', 'disarm', 'callback.event')
    m['events_at_kill'] = job_state(ca, job_id)['events']

    if args.variant == 'lost-lost':
        names = ['lost_instance.before_claim']
        arm(ca, 'heartbeat.force_lost', 'trigger', {'other': owner})
        parallel(lambda: trigger_heartbeat(ca), lambda: trigger_heartbeat(cb))
        log(f'seam: {a} and {b} both treat {owner} as lost; heartbeats triggered together')
        wait_hits(ca, 'lost_instance.before_claim', lambda h: h['action'] == 'pause', timeout=120, desc='a lost path to hold')
        time.sleep(5)
        # A second chance for the other node, while the first still holds the lock.
        parallel(lambda: trigger_heartbeat(ca), lambda: trigger_heartbeat(cb))
        time.sleep(15)
    else:
        arm(ca, 'heartbeat.force_lost', 'trigger', {'node': a, 'other': owner})
        log(f'seam: only {a} treats {owner} as lost; its claim is vetoed so it just marks {owner} offline ({trigger_heartbeat(ca)})')
        wait_for(f'{owner} marked offline', lambda: instances(ca)[owner]['state'] != 'ready', 180, poll=2)
        m['owner_offline_at'] = utcnow()
        log(f'{owner} is offline; the job is still running and still owned by {owner}: an orphan for every sweep')
        if args.variant == 'sweep-sweep':
            names = ['sweep.before_claim']
            arm(ca, 'sweep.before_claim', 'pause', {'job_id': job_id}, timeout=900)
            # Wait for each node's own periodic heartbeat, so each node has exactly one holder
            # (a triggered heartbeat close to a periodic one gives a node two). Trigger only a
            # node whose heartbeat has not come within one period.
            try:
                wait_for(
                    f'the periodic heartbeats of {a} and {b} to hold at sweep.before_claim',
                    lambda: {a, b} <= set(by_node(pause_hits(ca, 'sweep.before_claim'))),
                    70,
                    poll=1,
                )
            except TimeoutError:
                for host, cont in ((a, ca), (b, cb)):
                    if host not in by_node(pause_hits(ca, 'sweep.before_claim')):
                        log(f'{host} has no holder after 70 s; triggering its heartbeat ({trigger_heartbeat(cont)})')
                wait_for(f'both {a} and {b} held', lambda: {a, b} <= set(by_node(pause_hits(ca, 'sweep.before_claim'))), 60, poll=1)
        elif args.variant == 'lost-then-sweep':
            # Not a race: the interleaving seen in jobs 112 and 115, forced step by step on A.
            #  1. A's lost path holds before its claim (it keeps task_manager_lock).
            #  2. A's next heartbeat sweeps and claims; its adoption X is published and starts,
            #     but X's task id is held before it is saved (adoption.before_task_id_saved).
            #  3. The lost path resumes, fails its claim, and on the same heartbeat
            #     _process_running_jobs sees the job owned by A with a task id that is not running
            #     (the dead owner's), so it re-queues: held before publishing (adoption.before_queue).
            #  4. X's task id is saved. 5. The re-queue publishes: dispatcherd discards it as a
            #     duplicate of the running X, and _queue_job_adoption saves the discarded uuid.
            names = ['lost_instance.before_claim']
            arm(ca, 'lost_instance.before_claim', 'pause', {'job_id': job_id, 'node': a}, timeout=900)
            arm(ca, 'adoption.before_task_id_saved', 'pause', {'job_id': job_id, 'node': a}, timeout=900)
            arm(ca, 'sweep.before_claim', 'sleep', {'job_id': job_id}, seconds=0)
            trigger_heartbeat(ca)
            wait_hits(ca, 'lost_instance.before_claim', lambda h: h['action'] == 'pause', timeout=120, desc=f'{a} to hold in its lost path')
            log(f'step 1: {a} holds its lost path; triggering another heartbeat on {a} to sweep ({trigger_heartbeat(ca)})')
            x = wait_hits(ca, 'adoption.before_task_id_saved', timeout=120, desc=f'{a} to sweep, claim and publish X')[0]
            m['adoption_x'] = x['ctx'].get('task_id')
            log(f"step 2: {a} swept and published adoption X={m['adoption_x']}; its task id is held before it is saved")
            arm(ca, 'adoption.before_queue', 'pause', {'job_id': job_id, 'node': a}, timeout=900)
            release_together(ca, ['lost_instance.before_claim'], lead=1.0)
            wait_hits(ca, 'adoption.before_queue', lambda h: h['action'] == 'pause', timeout=120, desc='the lost path heartbeat to re-queue')
            log('step 3: the resumed heartbeat re-queues an adoption (held before publishing)')
            manage(ca, 'failpoint', 'disarm', 'adoption.before_task_id_saved')
            wait_for('X task id saved', lambda: job_state(ca, job_id)['celery_task_id'] == m['adoption_x'], 30, poll=1)
            log(f"step 4: job celery_task_id = X ({m['adoption_x']})")
            manage(ca, 'failpoint', 'disarm', 'adoption.before_queue')
            time.sleep(3)
            m['job_task_id_after_requeue'] = job_state(ca, job_id)['celery_task_id']
            log(f"step 5: re-queue published; job celery_task_id now {m['job_task_id_after_requeue']}")
        else:
            names = ['lost_instance.before_claim', 'sweep.before_claim']
            arm(ca, 'lost_instance.before_claim', 'pause', {'job_id': job_id, 'node': a}, timeout=900)
            # Any node's sweep holds: a periodic heartbeat on A (its lost path blocked by its own
            # held one, which keeps task_manager_lock) would otherwise sweep and claim unheld.
            arm(ca, 'sweep.before_claim', 'pause', {'job_id': job_id}, timeout=900)
            trigger_heartbeat(ca)
            wait_hits(ca, 'lost_instance.before_claim', lambda h: h['action'] == 'pause', timeout=120, desc=f'{a} to hold in its lost path')
            trigger_heartbeat(cb)
            wait_hits(ca, 'sweep.before_claim', lambda h: h['action'] == 'pause', timeout=120, desc=f'{b} to hold in its sweep')
        time.sleep(2)
    held = {n: by_node(pause_hits(ca, n)) for n in names}
    m['held'] = held
    m['held_total'] = sum(sum(v.values()) for v in held.values())
    log(f'held before the claim UPDATE: {held}')
    if args.variant != 'lost-then-sweep':
        rel = release_together(ca, names)
        m['release_at'] = rel['at_utc']
    try:
        wait_hits(ca, 'adoption.after_snapshot', timeout=180, desc='an adoption to start streaming')
    except TimeoutError as exc:
        notes.append(str(exc))
        m['invalid'] = 'no adoption after the release'
    time.sleep(15)  # a losing claimant's adoption, if any, has started by now
    snaps = fired_hits(ca, 'adoption.after_snapshot')
    if snaps:
        winner = container_for(snaps[0]['node'])
        m['adoption_task_uuids'] = running_tasks(winner)
        m['job_task_id'] = job_state(ca, job_id)['celery_task_id']
        m['job_task_id_is_running_adoption'] = m['job_task_id'] in m['adoption_task_uuids']
        log(f"job celery_task_id={m['job_task_id']}; adoption task(s) running on {winner}: {m['adoption_task_uuids']}")
    if args.cancel_in_adoption and snaps:
        res = cancel_job(ca, job_id)
        m['cancel_sent_to'] = f"{res['sent_to']['controller_node']}/{res['sent_to']['celery_task_id']}"
        m['cancel_hits_running_adoption'] = res['sent_to']['celery_task_id'] in m['adoption_task_uuids']
        notes.append(f"cancel during adoption at {res['at']}: sent to {m['cancel_sent_to']}; adoption task(s) running on {winner}: {m['adoption_task_uuids']}")
        log(notes[-1])
    rs = resumed(ca, names)
    m['resumed'] = rs
    wakes = [r['woke'] for r in rs if r['woke'] is not None]
    m['resume_spread_ms'] = round((max(wakes) - min(wakes)) * 1000, 3) if len(wakes) > 1 else None
    for name in names:
        arm(ca, name, 'sleep', {'job_id': job_id}, seconds=0)  # keep recording later attempts, hold nothing
    manage(ca, 'failpoint', 'disarm', 'heartbeat.force_lost')
    wait_finished(ca, job_id, args.finish_timeout)
    start_back(oc, owner)
    time.sleep(args.settle)
    m['claims_queued'] = by_node(fired_hits(ca, 'adoption.before_queue'))
    m['adoption_tasks'] = by_node(fired_hits(ca, 'adoption.after_claim'))
    m['streams_adopted'] = by_node(fired_hits(ca, 'adoption.after_snapshot'))
    m['adoption_finalize'] = by_node(fired_hits(ca, 'adoption.after_finalize_before_release'))
    m['unit_end'] = unit_status(unit)

    def from_logs(logs):
        counts = count_log_lines(logs, job_id, unit)
        sweeps_held = held.get('sweep.before_claim', {})
        sweep_won = counts['sweep_claimed']
        return {
            'log_counts': counts,
            'claims_succeeded': sum(counts['lost_claimed'].values()) + sum(sweep_won.values()),
            'claims_lost': sum(counts['lost_already_claimed'].values()) + sum(max(0, n - sweep_won.get(node, 0)) for node, n in sweeps_held.items()),
        }

    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=from_logs)


def scenario_adopter_dies(containers, args):
    """Adopter dies: the controller dies, its adopter dies too, and a third party adopts.

    1. A chatty job's controller O is held before event --seam-counter and killed.
    2. PR: adopter A1 (the next node) is told O is lost and claims; it is held either right
       after its claim (--hold-at claim, adoption.after_claim) or mid-stream before event
       --adopter-counter once every event before it is stored (--hold-at stream). A1 is killed.
    3. --variant third: the third control node T is told A1 is lost and adopts.
       --variant return: O is started again, told A1 is lost, and adopts (run with 2 nodes, so
       no third node can step in first).
    devel: nobody adopts across nodes; the lost-instance path reaps the job (the baseline).
    Measures: whether the second adoption happens, both snapshots, duplicates and gaps, final
    status, notifications, and how often the work unit is released (finalize hits) or never.
    """
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    if pr and args.variant == 'third' and len(containers) < 3:
        raise SystemExit('adopter-dies --variant third needs three control nodes')
    if pr and args.variant == 'return' and len(containers) != 2:
        raise SystemExit('adopter-dies --variant return needs exactly two control nodes (a third would adopt first)')
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    others = sorted(container_for_host(c) for c in containers if c != oc)
    a1 = others[0]
    ca1 = container_for(a1)
    m = {'owner': owner, 'adopter_1': a1, 'variant': args.variant, 'hold_at': args.hold_at, 'branch': 'PR' if pr else 'devel'}
    notes = [f"adopter-dies {args.variant} hold-at={args.hold_at} on {m['branch']}: owner {owner}, first adopter {a1}"]
    arm_hold(ca1, job_id, owner, args.seam_counter)
    arm_recorders(
        ca1,
        job_id,
        [
            'adoption.before_queue',
            'adoption.after_claim',
            'adoption.after_snapshot',
            'job.after_finalize_before_release',
            'adoption.after_finalize_before_release',
        ],
    )
    wait_hold(ca1, job_id, owner, args.seam_counter)
    wait_db_events(ca1, job_id, args.seam_counter)
    m['killed_owner_at'] = kill(oc)
    manage(ca1, 'failpoint', 'disarm', 'callback.event')
    m['events_at_owner_kill'] = job_state(ca1, job_id)['events']

    if not pr:
        s = watch(ca1, job_id, unit, args.finish_timeout, until=terminal, poll=5)
        m['owner_kill_to_terminal_s'] = round(time.time() - at_seconds(m['killed_owner_at']), 1)
        notes.append(
            f"devel: job terminal {m['owner_kill_to_terminal_s']}s after the kill: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}"
        )
        log(notes[-1])
        watch(
            ca1,
            job_id,
            unit,
            600,
            until=lambda _s: unit_status(unit).get('StateName') in ('Succeeded', 'Failed', 'Canceled') or 'error' in unit_status(unit),
            poll=15,
            label='after terminal',
        )
        m['unit_end'] = unit_status(unit)
        notes.append(f"exec-node unit after the job ended: {m['unit_end']}")
        start_back(oc, owner)
        time.sleep(args.settle)
        m['adoptions'] = [f"{h['node']} thr={h['ctx'].get('safe_threshold')}" for h in fired_hits(ca1, 'adoption.after_snapshot')]
        return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})

    if args.hold_at == 'claim':
        arm(ca1, 'adoption.after_claim', 'pause', {'job_id': job_id, 'node': a1}, timeout=1800)
    else:
        arm(ca1, 'callback.event', 'pause', {'job_id': job_id, 'node': a1, 'counter': args.adopter_counter}, timeout=1800)
    force_lost(ca1, a1, owner)
    if args.hold_at == 'claim':
        hold = wait_hits(ca1, 'adoption.after_claim', lambda h: h['action'] == 'pause', timeout=args.claim_timeout, desc=f'{a1} to claim and hold')[0]
    else:
        hold = wait_hits(
            ca1, 'callback.event', lambda h: h['node'] == a1 and str(h['ctx'].get('counter')) == str(args.adopter_counter), timeout=args.claim_timeout
        )[0]
        wait_db_events(ca1, job_id, args.adopter_counter)
    m['adopter_1_held_at'] = hold['at']
    manage(ca1, 'failpoint', 'disarm', 'heartbeat.force_lost')
    snaps = fired_hits(ca1, 'adoption.after_snapshot')
    m['snapshot_1'] = snaps[0]['ctx'].get('safe_threshold') if snaps else None
    js = job_state(ca1, job_id)
    m['events_at_adopter_kill'] = js['events']
    log(f"{a1} holds job {job_id} (controller={js['controller_node']}, {js['events']} events stored, snapshot {m['snapshot_1']})")

    if args.variant == 'third':
        second, cs = others[1], container_for(others[1])
    else:
        second, cs = owner, oc
    m['adopter_2_expected'] = second
    m['killed_adopter_1_at'] = kill(ca1)
    if args.variant == 'return':
        start_back(oc, owner)
    # The held caller died with the node; the second adopter must not hold anywhere.
    for name in ('adoption.after_claim', 'callback.event'):
        manage(cs, 'failpoint', 'disarm', name)
    arm_recorders(cs, job_id, ['adoption.after_claim'])
    n_snaps = len(snaps)

    def second_snapshot():
        return len(fired_hits(cs, 'adoption.after_snapshot')) > n_snaps

    arm(cs, 'heartbeat.force_lost', 'trigger', {'node': second, 'other': a1})
    t_end = time.monotonic() + args.claim_timeout
    while time.monotonic() < t_end and not second_snapshot():
        log(f'seam: {second} treats {a1} as lost; triggering its heartbeat ({trigger_heartbeat(cs)})')
        try:
            wait_for('the second adoption', second_snapshot, 20, poll=2)
        except TimeoutError:
            continue
    manage(cs, 'failpoint', 'disarm', 'heartbeat.force_lost')
    snaps = fired_hits(cs, 'adoption.after_snapshot')
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in snaps]
    m['second_adoption'] = len(snaps) > n_snaps
    if m['second_adoption']:
        m['adopter_2'] = snaps[-1]['node']
        m['snapshot_2'] = snaps[-1]['ctx'].get('safe_threshold')
        m['adopter_1_kill_to_snapshot_2_s'] = round(at_seconds(snaps[-1]['at']) - at_seconds(m['killed_adopter_1_at']), 1)
    else:
        notes.append(f'no second adoption within {args.claim_timeout}s')
    s = watch(cs, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    watch(
        cs,
        job_id,
        unit,
        300,
        until=lambda _s: 'error' in unit_status(unit) or unit_status(unit).get('StateName') in ('Succeeded', 'Failed', 'Canceled'),
        poll=15,
        label='after terminal',
    )
    for c, h in ((ca1, a1), (oc, owner)):
        if manage(c, 'failpoint', 'list', check=False).returncode != 0:
            start_back(c, h)
    time.sleep(args.settle)
    m['unit_end'] = unit_status(unit)
    m['adoption_tasks'] = by_node(fired_hits(cs, 'adoption.after_claim'))
    m['claims_queued'] = by_node(fired_hits(cs, 'adoption.before_queue'))
    m['finalize_then_release'] = by_node(fired_hits(cs, 'adoption.after_finalize_before_release')) | {
        f"{k} (job task)": v for k, v in by_node(fired_hits(cs, 'job.after_finalize_before_release')).items()
    }
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


# --- workflow orphan -----------------------------------------------------------------------

WF_NAME = 'failpoint workflow'


def wf_setup(containers, args):
    """A (chatty, --iterations) --success--> B, --failure--> C (both 3 iterations)."""
    pb = getattr(args, 'a_playbook', 'chatty.yml')
    jt_a = setup(containers, 'failpoint wf A' if pb == 'chatty.yml' else f'failpoint wf A {pb}', pb, {'iterations': args.iterations})
    jt_b = setup(containers, 'failpoint wf B success', 'chatty.yml', {'iterations': 3}, allow_simultaneous=True)
    jt_c = setup(containers, 'failpoint wf C failure', 'chatty.yml', {'iterations': 3}, allow_simultaneous=True)
    return orm(
        containers[0],
        f'''
from awx.main.models import Organization, WorkflowJobTemplate, WorkflowJobTemplateNode, NotificationTemplate
org = Organization.objects.get(name='Default')
wf, _ = WorkflowJobTemplate.objects.get_or_create(name={WF_NAME!r}, defaults=dict(organization=org))
wf.workflow_job_template_nodes.all().delete()
a = WorkflowJobTemplateNode.objects.create(workflow_job_template=wf, unified_job_template_id={jt_a}, identifier='A')
b = WorkflowJobTemplateNode.objects.create(workflow_job_template=wf, unified_job_template_id={jt_b}, identifier='B')
c = WorkflowJobTemplateNode.objects.create(workflow_job_template=wf, unified_job_template_id={jt_c}, identifier='C')
a.success_nodes.add(b)
a.failure_nodes.add(c)
nt = NotificationTemplate.objects.get(name='failpoint webhook')
wf.notification_templates_success.add(nt)
wf.notification_templates_error.add(nt)
emit(dict(wf=wf.id, a={jt_a}, b={jt_b}, c={jt_c}))
''',
    )


def wf_launch(container, wf_id):
    return orm(
        container,
        f'''
from awx.main.models import WorkflowJobTemplate
wj = WorkflowJobTemplate.objects.get(pk={wf_id}).create_unified_job()
wj.signal_start()
emit(wj.id)
''',
    )


def wf_state(container, wj_id, ids):
    return orm(
        container,
        f'''
from awx.main.models import WorkflowJob, UnifiedJob
wj = WorkflowJob.objects.get(pk={wj_id})
nodes = {{}}
for n in wj.workflow_job_nodes.all():
    j = n.job
    nodes[n.identifier] = dict(job=j.id if j else None, status=j.status if j else None, do_not_run=n.do_not_run,
                               created=j.created if j else None, finished=j.finished if j else None)
def spawned(tid):
    return [dict(id=j.id, status=j.status, created=j.created) for j in UnifiedJob.objects.filter(unified_job_template_id=tid, created__gte=wj.created).order_by('id')]
def _status(body):
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except ValueError:
            return None
    return body.get('status') if isinstance(body, dict) else None
arts = {{}}
for n in wj.workflow_job_nodes.all():
    if n.job:
        real = n.job.get_real_instance()
        arts[n.identifier] = dict(artifacts=getattr(real, 'artifacts', None), fp_artifact=json.loads(real.extra_vars or '{{}}').get('fp_artifact'))
emit(dict(status=wj.status, finished=wj.finished, explanation=wj.job_explanation, nodes=nodes, artifacts=arts,
          b_jobs=spawned({ids['b']}), c_jobs=spawned({ids['c']}),
          notifications=[_status(n.body) for n in wj.notifications.all().order_by('created')]))
''',
    )


def scenario_workflow_orphan(containers, args):
    """Workflow orphan: node A's job is orphaned mid-run; does the workflow act once, and on the truth?

    Workflow: A (chatty) -> on success B, on failure C (short jobs). Two control nodes.
      --variant slow  A's controller O misses heartbeats while alive (heartbeat.start pause).
                      PR --mode seam: O held before event --seam-counter, the peer's lost check
                      forced, both controllers stream, and the second finalizer (--order) held at
                      callback.artifacts until the first has finalized. devel (timing): the
                      peer's natural is_lost decides (devel reaps A 'failed' while it still runs).
      --variant kill  O is held before event --seam-counter and killed (left down until A ends).
                      PR: the peer is told O is lost and adopts. devel: the lost path reaps.
    Measures: B and C jobs launched (double automation), workflow status and notifications,
    and whether A's final status matches the branch the workflow took.
    """
    if len(containers) != 2:
        raise SystemExit('workflow-orphan needs exactly two control nodes')
    c0 = containers[0]
    have = registry(c0)
    pr = 'sweep.before_claim' in have
    seam = args.mode == 'seam'
    if seam and not pr:
        raise SystemExit('--mode seam needs the PR branch (heartbeat.force_lost, callback.artifacts)')
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    ids = wf_setup(containers, args)
    since = since_now()
    wj = wf_launch(c0, ids['wf'])
    log(f"launched workflow job {wj} from {WF_NAME!r} {ids}")

    def a_running():
        s = wf_state(c0, wj, ids)['nodes'].get('A') or {}
        if s.get('job') and s.get('status') == 'running':
            js = job_state(c0, s['job'])
            return js['work_unit_id'] and dict(js, id=s['job'])
        return None

    st = wait_for('node A job running with a work unit', a_running, 300, poll=3)
    job_id, owner, unit = st['id'], st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    ph = container_for_host(peer)
    m = {'workflow_job': wj, 'a_job': job_id, 'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel'}
    notes = [f"workflow-orphan {args.variant} mode={args.mode} on {m['branch']}: workflow job {wj}, A job {job_id} on {owner}"]
    held = seam or args.variant == 'kill'
    if held:
        arm_hold(c0, job_id, owner, args.seam_counter)
    arm_recorders(c0, job_id, ['adoption.after_snapshot', 'job.after_finalize_before_release', 'adoption.after_finalize_before_release'])

    if args.variant == 'slow':
        second = None
        if seam:
            second = owner if args.order == 'adopter-first' else ph
            arm(c0, 'callback.artifacts', 'pause', {'job_id': job_id, 'node': second}, timeout=1800)
            wait_hold(c0, job_id, owner, args.seam_counter)
            wait_db_events(c0, job_id, args.seam_counter)
        arm(c0, 'heartbeat.start', 'pause', {'node': owner, 'periodic': True}, timeout=1200)
        hb = wait_hits(c0, 'heartbeat.start', timeout=120)[0]
        m['heartbeat_paused_at'] = hb['at']
        log(f'{owner} heartbeat paused')
        try:
            if seam:
                force_lost(c0, ph, owner)
                snap = wait_hits(c0, 'adoption.after_snapshot', timeout=args.claim_timeout)[0]
                m['snapshot'] = f"{snap['node']} thr={snap['ctx'].get('safe_threshold')} at {snap['at']}"
                manage(c0, 'failpoint', 'disarm', 'heartbeat.force_lost')
                manage(c0, 'failpoint', 'disarm', 'callback.event')
            else:
                # devel: the peer decides on its own once O's last_seen passes is_lost.
                s = wait_for(
                    'the peer to claim or reap A',
                    lambda: ((x := job_state(c0, job_id))['status'] != 'running' or x['controller_node'] != owner) and x or None,
                    args.claim_timeout,
                    poll=3,
                )
                m['peer_decision'] = f"status={s['status']} controller={s['controller_node']} at {utcnow()}"
                log(f"peer decided: {m['peer_decision']}")
        finally:
            manage(c0, 'failpoint', 'release', 'heartbeat.start', check=False)
            manage(c0, 'failpoint', 'disarm', 'heartbeat.start', check=False)
            log(f'released {owner} heartbeat')
        if seam:
            first_hit = 'job.after_finalize_before_release' if second == ph else 'adoption.after_finalize_before_release'
            h = wait_hits(c0, first_hit, timeout=args.finish_timeout, poll=3)[0]
            log(f'seam: first finalizer done ({first_hit} on {h["node"]}); releasing {second}')
            manage(c0, 'failpoint', 'disarm', 'callback.artifacts')
    else:
        wait_hold(c0, job_id, owner, args.seam_counter)
        wait_db_events(c0, job_id, args.seam_counter)
        m['killed_at'] = kill(oc)
        manage(peer, 'failpoint', 'disarm', 'callback.event')
        if pr:
            force_lost(peer, ph, owner)
            try:
                snap = wait_hits(peer, 'adoption.after_snapshot', timeout=args.claim_timeout)[0]
                m['snapshot'] = f"{snap['node']} thr={snap['ctx'].get('safe_threshold')} at {snap['at']}"
            except TimeoutError as exc:
                notes.append(str(exc))
            manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost')
    cw = peer if args.variant == 'kill' else c0
    wait_for(
        'workflow job terminal', lambda: (w := wf_state(cw, wj, ids))['status'] not in ('pending', 'waiting', 'running') and w, args.finish_timeout, poll=10
    )
    wait_finished(cw, job_id, args.finish_timeout)
    if args.variant == 'kill':
        start_back(oc, owner)
    time.sleep(args.settle)
    w = wf_state(cw, wj, ids)
    a_final = job_state(cw, job_id)['status']
    took = sorted(x for x, k in (('B', 'b_jobs'), ('C', 'c_jobs')) if w[k])
    m.update(
        workflow_status=w['status'],
        workflow_notifications=w['notifications'],
        b_jobs=len(w['b_jobs']),
        c_jobs=len(w['c_jobs']),
        branches_taken=took,
        a_final_status=a_final,
        nodes=w['nodes'],
        acted_matches_final=(took == ['B']) == (a_final == 'successful') and len(took) == 1,
        artifacts=w.get('artifacts'),
    )
    notes.append(f'workflow {wj}: {json.dumps(w, default=str)}')
    log(f"workflow {wj} {w['status']}: B jobs {len(w['b_jobs'])}, C jobs {len(w['c_jobs'])}, A final {a_final}")
    out_name = f'{run_label(args)}-wf{wj}-job{job_id}'
    return report(
        containers, job_id, since, args, unit, notes, metrics=m, out_name=out_name, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)}
    )


# --- many orphans --------------------------------------------------------------------------


def dispatcher_workers(container):
    """Dispatcher pool on a node: workers, busy workers, and what the busy ones run."""
    out = run(['docker', 'exec', container, 'awx-manage', 'dispatcherctl', 'workers'], check=False).stdout
    tasks = [t.strip().strip("'\"") for t in re.findall(r'^\s+current_task: (.*)$', out, re.M)]
    busy = [t for t in tasks if t not in ('null', '', 'None')]
    return {
        'workers': len(tasks),
        'busy': len(busy),
        'adopt': sum('adopt_job_async' in t for t in busy),
        'tasks': dict(Counter(t.rsplit('.', 1)[-1] for t in busy)),
    }


def running_tasks(container, task='adopt_job_async'):
    """uuids of the dispatcher workers on a node currently running `task`."""
    out = run(['docker', 'exec', container, 'awx-manage', 'dispatcherctl', 'workers'], check=False).stdout
    pairs = re.findall(r'^\s+current_task: (.*)\n\s+current_task_uuid: (.*)$', out, re.M)
    return [u.strip().strip("'\"") for t, u in pairs if task in t]


def job_statuses(container, job_ids):
    """{job id: status fields}; ids come back as ints (JSON object keys are strings)."""
    return {int(k): v for k, v in _job_statuses(container, job_ids).items()}


def _job_statuses(container, job_ids):
    return orm(
        container,
        f'''
from awx.main.models import UnifiedJob
emit({{j.id: dict(status=j.status, controller=j.controller_node, explanation=j.job_explanation, started=j.started, finished=j.finished, created=j.created)
      for j in UnifiedJob.objects.filter(pk__in={list(job_ids)!r})}})
''',
    )


def scenario_many_orphans(containers, args):
    """Many orphans: --orphans jobs controlled by awx-1 when it dies; awx-2 adopts (PR) or reaps (devel).

    Two control nodes. awx-2 is disabled while the jobs are placed, so all go to awx-1, then
    re-enabled. awx-1 is killed and left down; PR --mode seam tells awx-2 at once that awx-1 is
    lost (otherwise the natural is_lost decides). While the orphans are handled, a sampler
    records awx-2's dispatcher pool (workers, busy, busy with adopt_job_async) every
    --sample seconds, and two probes measure whether unrelated work is delayed: a new short job
    and a Demo Project update, launched once the first orphan has been claimed or reaped.
    """
    if len(containers) != 2:
        raise SystemExit('many-orphans needs exactly two control nodes')
    c = 'tools_awx_2'
    pr = 'sweep.before_claim' in registry(c)
    seam = args.mode == 'seam' and pr
    manage(c, 'failpoint', 'disarm', '--all')
    manage(c, 'failpoint', 'clear-hits')
    since = since_now()
    m = {'branch': 'PR' if pr else 'devel', 'orphans_requested': args.orphans, 'iterations': args.iterations}
    notes = [f"many-orphans on {m['branch']}: {args.orphans} jobs of chatty.yml x{args.iterations}"]
    m['awx_2_max_workers'] = orm(c, 'from awx.main.utils.common import get_auto_max_workers\nemit(get_auto_max_workers())\n')
    set_instance(c, 'awx-2', enabled=False)
    wait_for('awx-2 capacity 0', lambda: instances(c)['awx-2']['capacity'] == 0, 180, poll=5)
    jt = setup(containers, 'failpoint orphan', 'chatty.yml', {'iterations': args.iterations}, allow_simultaneous=True)
    # Templates for the probes are created now: setup() copies the playbooks into every
    # control container, and awx-1 will be dead when the probes launch.
    probe_jt = setup(containers, 'failpoint probe', 'chatty.yml', {'iterations': 3}, allow_simultaneous=True)
    jobs = orm(
        c,
        f'''
from awx.main.models import JobTemplate
jt = JobTemplate.objects.get(pk={jt})
ids = []
for _ in range({args.orphans}):
    job = jt.create_unified_job()
    job.signal_start()
    ids.append(job.id)
emit(ids)
''',
    )
    log(f'launched {len(jobs)} jobs: {jobs[0]}..{jobs[-1]}')

    def all_running():
        st = job_statuses(c, jobs)
        n = sum(1 for s in st.values() if s['status'] == 'running')
        return n == len(jobs) and st

    try:
        st = wait_for(f'all {len(jobs)} jobs running', all_running, 600, poll=10)
    finally:
        set_instance(c, 'awx-2', enabled=True)
    m['launch_to_all_running_s'] = round(max(at_seconds(s['started']) for s in st.values()) - min(at_seconds(s['created']) for s in st.values()), 1)
    m['controllers'] = dict(Counter(s['controller'] for s in st.values()))
    log(f"all running: controllers {m['controllers']}; awx-2 re-enabled")
    if set(m['controllers']) != {'awx-1'}:
        m['invalid'] = f"not all jobs controlled by awx-1: {m['controllers']}"
    wait_for('awx-2 capacity back', lambda: instances(c)['awx-2']['capacity'] > 0, 180, poll=5)
    m['exec_playbooks_before_kill'] = len(exec_node_processes(r'ansible-playbook'))
    arm_recorders(c, None, ['adoption.before_queue', 'adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])

    samples = []
    stop = threading.Event()

    def sampler():
        while not stop.is_set():
            try:
                w = dispatcher_workers(c)
                st = job_statuses(c, jobs)
                w['at'] = utcnow()
                w['jobs'] = dict(Counter(s['status'] for s in st.values()))
                w['adopted_by_awx_2'] = sum(1 for s in st.values() if s['controller'] == 'awx-2')
                samples.append(w)
            except Exception as exc:  # a sample lost to a restarting container is not fatal
                samples.append({'at': utcnow(), 'error': str(exc)[:200]})
            stop.wait(args.sample)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    time.sleep(args.lead)
    m['killed_at'] = kill('tools_awx_1')
    if seam:
        force_lost(c, 'awx-2', 'awx-1')

    def first_decision():
        st = job_statuses(c, jobs)
        return any(s['controller'] != 'awx-1' or s['status'] != 'running' for s in st.values()) or None

    wait_for('the first orphan to be claimed or reaped', first_decision, args.claim_timeout, poll=2)
    m['first_decision_at'] = utcnow()
    probe_job = launch(c, probe_jt)
    probe_pu = orm(c, "from awx.main.models import Project\npu = Project.objects.get(name='Demo Project').update()\nemit(pu.id if pu else None)\n")
    m['probe_launched_at'] = utcnow()
    log(f'probes launched: job {probe_job}, project update {probe_pu}')

    def all_terminal():
        st = job_statuses(c, jobs + [probe_job] + ([probe_pu] if probe_pu else []))
        return all(s['status'] not in ('pending', 'waiting', 'running') for s in st.values()) and st

    try:
        final = wait_for('every orphan and probe terminal', all_terminal, args.finish_timeout, poll=10)
    except TimeoutError as exc:
        notes.append(str(exc))
        final = job_statuses(c, jobs + [probe_job] + ([probe_pu] if probe_pu else []))
    if seam:
        manage(c, 'failpoint', 'disarm', 'heartbeat.force_lost')
    # Keep sampling a little after the end: do adoption workers leak (stay busy)?
    time.sleep(max(args.settle, 3 * args.sample))
    stop.set()
    th.join()
    orphans = {j: final[j] for j in jobs}
    kill_s = at_seconds(m['killed_at'])
    m['outcome'] = {
        'adopted': sum(1 for s in orphans.values() if s['controller'] == 'awx-2' and s['status'] not in ('pending', 'waiting', 'running')),
        'reaped': sum(1 for s in orphans.values() if 'reaped' in (s['explanation'] or '')),
        'stranded': sum(1 for s in orphans.values() if s['status'] in ('pending', 'waiting', 'running')),
        'statuses': dict(Counter(s['status'] for s in orphans.values())),
    }
    ends = [at_seconds(s['finished']) for s in orphans.values() if s['finished']]
    m['kill_to_all_terminal_s'] = round(max(ends) - kill_s, 1) if ends and not m['outcome']['stranded'] else None
    for key, jid in (('probe_job', probe_job), ('probe_project_update', probe_pu)):
        if jid:
            s = final[jid]
            m[key] = dict(
                id=jid,
                status=s['status'],
                controller=s['controller'],
                wait_s=round(at_seconds(s['started']) - at_seconds(s['created']), 1) if s['started'] else None,
                total_s=round(at_seconds(s['finished']) - at_seconds(s['created']), 1) if s['finished'] else None,
            )
    ok_samples = [s for s in samples if 'workers' in s]
    m['pool'] = {
        'max_workers': m['awx_2_max_workers'],
        'peak_workers': max((s['workers'] for s in ok_samples), default=None),
        'peak_busy': max((s['busy'] for s in ok_samples), default=None),
        'peak_adopt': max((s['adopt'] for s in ok_samples), default=None),
        'adopt_busy_after_all_terminal': ok_samples[-1]['adopt'] if ok_samples else None,
    }
    m['snapshots'] = len(fired_hits(c, 'adoption.after_snapshot')) if pr else 0
    m['adoption_tasks'] = len(fired_hits(c, 'adoption.after_claim')) if pr else 0
    start_back('tools_awx_1', 'awx-1')
    # devel's reaped orphans keep running unseen on the execution node; let them drain so the
    # next run starts clean.
    wait_for('execution node playbooks to drain', lambda: not exec_node_processes(r'ansible-playbook') or None, args.finish_timeout, poll=15)
    time.sleep(args.settle)
    invariants = {}
    failed_by_check = Counter()
    for j in jobs:
        res = json.loads(manage(c, 'failpoint', 'check-job', str(j)).stdout)
        bad = sorted(chk['name'] for chk in res['checks'] if not chk['ok'])
        invariants[j] = bad
        failed_by_check.update(bad)
    m['invariants_failed_by_check'] = dict(failed_by_check)
    m['jobs_with_any_failure'] = sum(1 for v in invariants.values() if v)
    if args.out:
        out_dir = os.path.join(args.out, f'{run_label(args)}-n{len(jobs)}-job{jobs[0]}')
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'many.json'), 'w') as fh:
            json.dump(
                {'jobs': orphans, 'probes': {k: m.get(k) for k in ('probe_job', 'probe_project_update')}, 'samples': samples, 'invariants': invariants},
                fh,
                indent=2,
                default=str,
            )
    notes.append(f"outcome {m['outcome']}; pool {m['pool']}; probes {m.get('probe_job')} {m.get('probe_project_update')}")
    log(notes[-1])
    unit = job_state(c, jobs[0])['work_unit_id']
    return report(containers, jobs[0], since, args, unit, notes, metrics=m, out_name=f'{run_label(args)}-n{len(jobs)}-job{jobs[0]}')


# --- Part 3, extra queue -------------------------------------------------------------------


def peer_of(containers, owner):
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    return oc, peer, container_for_host(peer)


def unit_end(c, job_id, unit, seconds=420):
    """Wait until the exec-node unit is terminal or gone; return what receptor-1 says."""
    if not unit:
        return {'error': 'no work unit id'}
    watch(
        c,
        job_id,
        unit,
        seconds,
        until=lambda _s: 'error' in unit_status(unit) or unit_status(unit).get('StateName') in ('Succeeded', 'Failed', 'Canceled'),
        poll=15,
        label='after terminal',
    )
    return unit_status(unit)


def ensure_up(containers):
    for c in containers:
        if manage(c, 'failpoint', 'list', check=False).returncode != 0:
            start_back(c, container_for_host(c))


def orphan_owner(peer, ph, owner, job_id, args, m, pr, counter=None):
    """Seam: the owner is held before event `counter` (armed by arm_hold), its events before
    that are stored, then it is killed and left down; on the PR the peer is told at once."""
    counter = counter or args.seam_counter
    wait_hold(peer, job_id, owner, counter)
    wait_db_events(peer, job_id, counter)
    m['killed_at'] = kill(container_for(owner))
    manage(peer, 'failpoint', 'disarm', 'callback.event')
    m['events_at_kill'] = job_state(peer, job_id)['events']
    if pr:
        force_lost(peer, ph, owner)


def finish_and_report(containers, peer, job_id, unit, since, args, notes, m, pr, oc=None, owner=None):
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    m['kill_to_terminal_s'] = round(time.time() - at_seconds(m['killed_at']), 1) if m.get('killed_at') else None
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    m['unit_end'] = unit_end(peer, job_id, unit)
    ensure_up(containers)
    time.sleep(args.settle)
    snaps = fired_hits(peer, 'adoption.after_snapshot')
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in snaps]
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def need_two(containers, name):
    if len(containers) != 2:
        raise SystemExit(f'{name} needs exactly two control nodes')


def scenario_claim_no_queue(containers, args):
    """Claim, then no queue: the claim UPDATE commits but publishing adopt_job_async fails.

    PR only (devel has no cross-controller claim). Two control nodes. The owner is held before
    event --seam-counter and killed; the peer is told it is lost.
      --variant lost           the lost-instance path claims; adoption.before_queue raises once
                               (after the claim, before adopt_job_async is published)
      --variant sweep          the lost path only marks the owner offline (its claim vetoed);
                               the sweep claims and adoption.before_queue raises once
      --variant after-publish  the lost path claims and publishes; saving the task id raises once
                               (adoption.before_task_id_saved)
    Watches --observe seconds for a retry (an adoption snapshot) and records the final status.
    """
    need_two(containers, 'claim-no-queue')
    c0 = containers[0]
    if 'sweep.before_claim' not in registry(c0):
        raise SystemExit('claim-no-queue needs the PR branch: devel never claims a lost peer job')
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant}
    notes = [f'claim-no-queue {args.variant}: owner {owner}, peer {ph}']
    arm_hold(peer, job_id, owner, args.seam_counter)
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    inject = 'adoption.before_task_id_saved' if args.variant == 'after-publish' else 'adoption.before_queue'
    arm(peer, inject, 'raise', {'job_id': job_id, 'node': ph}, times=1)
    if args.variant == 'sweep':
        arm(peer, 'lost_instance.before_claim', 'raise', {'job_id': job_id})
    orphan_owner(peer, ph, owner, job_id, args, m, True)
    h = wait_hits(peer, inject, lambda h: h['action'] == 'raise', timeout=args.claim_timeout)[0]
    m['injected_at'] = h['at']
    manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost')
    time.sleep(2)
    s = job_state(peer, job_id)
    m['after_injection'] = {k: s[k] for k in ('status', 'controller_node', 'celery_task_id', 'job_explanation')}
    log(f"{inject} raised at {h['at']}; job now {m['after_injection']}")

    def retried():
        if fired_hits(peer, 'adoption.after_snapshot'):
            return 'adopted'
        return terminal(job_state(peer, job_id)) and 'terminal'

    try:
        what = wait_for('an adoption retry or a terminal status', retried, args.observe, poll=5)
        m['outcome_within_observe'] = what
    except TimeoutError:
        m['outcome_within_observe'] = f'stranded: no adoption and not terminal after {args.observe}s'
        notes.append(m['outcome_within_observe'])
    snaps = fired_hits(peer, 'adoption.after_snapshot')
    if snaps:
        m['retry_after_s'] = round(at_seconds(snaps[0]['at']) - at_seconds(h['at']), 1)
        m['retry_node'] = snaps[0]['node']
    return finish_and_report(containers, peer, job_id, unit, since, args, notes, m, True)


def scenario_both_controllers_lost(containers, args):
    """Both controllers lost: kill both control nodes, wait --down seconds (past is_lost), bring one back.

      --variant peer-returns   the node that did not control the job comes back
      --variant owner-returns  the job's controller comes back
    Nothing is forced: this is about the real lost threshold and startup paths. Measures who
    adopts or reaps, when (strand length from the kill), and the final status.
    """
    need_two(containers, 'both-controllers-lost')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'down_s': args.down}
    notes = [f"both-controllers-lost {args.variant} on {m['branch']}: owner {owner}"]
    arm_hold(peer, job_id, owner, args.seam_counter)
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    wait_hold(peer, job_id, owner, args.seam_counter)
    wait_db_events(peer, job_id, args.seam_counter)
    manage(peer, 'failpoint', 'disarm', 'callback.event')
    m['killed_at'] = kill(oc)
    m['peer_killed_at'] = kill(peer)
    log(f'both control nodes down; waiting {args.down}s')
    time.sleep(args.down)
    back, bh = (peer, ph) if args.variant == 'peer-returns' else (oc, owner)
    m['returned'] = bh
    m['restart_at'] = utcnow()
    start_back(back, bh)
    s = watch(back, job_id, unit, args.finish_timeout, until=terminal, poll=5)
    m['kill_to_terminal_s'] = round(time.time() - at_seconds(m['killed_at']), 1)
    snaps = fired_hits(back, 'adoption.after_snapshot')
    if snaps:
        m['adopted_by'] = snaps[0]['node']
        m['kill_to_adoption_s'] = round(at_seconds(snaps[0]['at']) - at_seconds(m['killed_at']), 1)
        m['restart_to_adoption_s'] = round(at_seconds(snaps[0]['at']) - at_seconds(m['restart_at']), 1)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    m['unit_end'] = unit_end(back, job_id, unit)
    ensure_up(containers)
    time.sleep(args.settle)
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in fired_hits(back, 'adoption.after_snapshot')]
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_exec_node_dies(containers, args):
    """Exec node dies while orphaned: the controller is killed, then receptor-1 is restarted
    (--variant restart) or killed and started 20 s later (--variant kill-start) before anyone
    adopts. PR: the peer is then told the owner is lost and adopts a unit that was reset. devel:
    the lost-instance path decides. Watches --observe seconds; a job still running then is
    recorded as stranded and canceled to clean up."""
    need_two(containers, 'exec-node-dies')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel'}
    notes = [f"exec-node-dies {args.variant} on {m['branch']}: owner {owner}, unit {unit}"]
    arm_hold(peer, job_id, owner, args.seam_counter)
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    wait_hold(peer, job_id, owner, args.seam_counter)
    wait_db_events(peer, job_id, args.seam_counter)
    m['killed_at'] = kill(oc)
    manage(peer, 'failpoint', 'disarm', 'callback.event')
    m['unit_before_exec_restart'] = unit_status(unit)
    if args.variant == 'restart':
        run(['docker', 'restart', EXEC_CONTAINER])
    else:
        run(['docker', 'kill', EXEC_CONTAINER])
        time.sleep(20)
        run(['docker', 'start', EXEC_CONTAINER])
    m['exec_restarted_at'] = utcnow()
    log(f'{EXEC_CONTAINER} {args.variant} done')
    wait_for(f'{ph} to route to receptor-1 again', lambda: mesh_sees(peer, 'receptor-1'), 180, poll=3)
    m['unit_after_exec_restart'] = unit_status(unit)
    m['playbooks_after_exec_restart'] = len(exec_node_processes(r'ansible-playbook'))
    log(f"unit after the exec-node restart: {m['unit_after_exec_restart']}; playbook processes: {m['playbooks_after_exec_restart']}")
    if pr:
        force_lost(peer, ph, owner)
    s = watch(peer, job_id, unit, args.observe, until=terminal, poll=10)
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost')
    if not terminal(s):
        m['stranded'] = f"still {s['status']} {args.observe}s after the adoption trigger (controller {s['controller_node']}, {s['events']} events)"
        notes.append(m['stranded'])
        log(m['stranded'])
        res = cancel_job(peer, job_id)
        notes.append(f'canceled to clean up at {res["at"]}')
        s = watch(peer, job_id, unit, 300, until=terminal, poll=10)
        m['after_cancel'] = f"{s['status']} {s['job_explanation']!r}"
    m['final_explanation'] = s['job_explanation']
    m['unit_end'] = unit_status(unit)
    ensure_up(containers)
    time.sleep(args.settle)
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in fired_hits(peer, 'adoption.after_snapshot')]
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_job_timeout(containers, args):
    """Job timeout while orphaned: a template with timeout=--job-timeout, orphaned partway through.

      --variant none  baseline: no fault; how a timeout normally ends the job
      --variant kill  the owner is held before event --seam-counter and killed; PR: the peer adopts
    Measures when and how the job ended against the timeout (status, explanation, runtime).
    """
    need_two(containers, 'job-timeout')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    since = since_now()
    job_id, st = start_job(containers, args, jt_name='failpoint timeout', jt_fields={'timeout': args.job_timeout})
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'timeout_s': args.job_timeout}
    notes = [f"job-timeout {args.variant} on {m['branch']}: timeout {args.job_timeout}s, playbook {args.iterations}s"]
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    if args.variant == 'kill':
        arm_hold(peer, job_id, owner, args.seam_counter)
        orphan_owner(peer, ph, owner, job_id, args, m, pr)
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=5)
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    t = orm(
        peer,
        f'from awx.main.models import Job\nj = Job.objects.get(pk={job_id})\nemit(dict(started=j.started, finished=j.finished, elapsed=j.elapsed, timed_out=j.job_explanation))\n',
    )
    m['started'], m['finished'] = t['started'], t['finished']
    m['runtime_s'] = round(at_seconds(t['finished']) - at_seconds(t['started']), 1) if t['finished'] else None
    notes.append(f"job terminal: status={s['status']} after {m['runtime_s']}s (timeout {args.job_timeout}s); explanation={s['job_explanation']!r}")
    m['unit_end'] = unit_end(peer, job_id, unit)
    m['unit_detail'] = m['unit_end'].get('Detail')
    ensure_up(containers)
    time.sleep(args.settle)
    m['adoptions'] = [f"{h['node']}@{h['at']}" for h in fired_hits(peer, 'adoption.after_snapshot')]
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def host_facts(container, inventory='Demo Inventory', reset=False):
    return orm(
        container,
        f'''
from awx.main.models import Inventory
inv = Inventory.objects.get(name={inventory!r})
out = {{}}
for h in inv.hosts.all():
    if {reset!r}:
        h.ansible_facts = {{}}
        h.ansible_facts_modified = None
        h.save(update_fields=['ansible_facts', 'ansible_facts_modified'])
    out[h.name] = dict(keys=len(h.ansible_facts or {{}}), modified=h.ansible_facts_modified,
                       hostname=(h.ansible_facts or {{}}).get('ansible_hostname'), date=((h.ansible_facts or {{}}).get('ansible_date_time') or {{}}).get('iso8601'))
emit(out)
''',
    )


def scenario_fact_cache(containers, args):
    """Fact cache: a use_fact_cache job that gathers facts, adopted cross-node.

      --variant none  baseline: facts saved by a normal run
      --variant kill  the owner is held before event --seam-counter (facts already gathered) and
                      killed; PR: the peer adopts
    Host facts are cleared before the run and compared after it (keys, ansible_facts_modified
    against the job's start, the gathered date).
    """
    need_two(containers, 'fact-cache')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    before = host_facts(c0, reset=True)
    since = since_now()
    job_id, st = start_job(
        containers, args, jt_name='failpoint facts', playbook='facts.yml', extra_vars={'iterations': args.iterations}, jt_fields={'use_fact_cache': True}
    )
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'facts_before': before}
    notes = [f"fact-cache {args.variant} on {m['branch']}"]
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    if args.variant == 'kill':
        arm_hold(peer, job_id, owner, args.seam_counter)
        orphan_owner(peer, ph, owner, job_id, args, m, pr)
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    ensure_up(containers)
    time.sleep(args.settle)
    after = host_facts(peer)
    js = orm(peer, f'from awx.main.models import Job\nj = Job.objects.get(pk={job_id})\nemit(dict(started=j.started, finished=j.finished))\n')
    m['facts_after'] = after
    m['facts_saved'] = {h: bool(v['keys']) and v['modified'] is not None and at_seconds(v['modified']) >= at_seconds(js['started']) for h, v in after.items()}
    notes.append(f"job {s['status']}; facts after: {after}; saved by this job: {m['facts_saved']}")
    m['adoptions'] = [f"{h['node']}@{h['at']}" for h in fired_hits(peer, 'adoption.after_snapshot')]
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_set_stats_artifacts(containers, args):
    """set_stats artifacts: workflow-orphan with node A running setstats.yml (set_stats
    fp_artifact before the first tick). Same variants and orders as workflow-orphan; adds A's
    artifacts and the fp_artifact extra var node B received."""
    args.a_playbook = 'setstats.yml'
    return scenario_workflow_orphan(containers, args)


def scenario_job_slicing(containers, args):
    """Job slicing: a template with job_slice_count=2 over the 5-host inventory; slice 1's
    controller is held before event --seam-counter and killed (PR: the peer adopts). Checks that
    each slice's events and host summaries name only that slice's hosts, with the job-start ids."""
    need_two(containers, 'job-slicing')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    original = hostmap_inventory(c0)
    jt = setup(containers, 'failpoint sliced', 'chatty.yml', {'iterations': args.iterations}, inventory=HOSTMAP_INV, jt_fields={'job_slice_count': 2})
    since = since_now()
    wf = launch(c0, jt)
    log(f'launched sliced job (workflow job {wf}) over {original}')

    def slices():
        out = orm(
            c0,
            f'''
from awx.main.models import WorkflowJob
wj = WorkflowJob.objects.get(pk={wf})
emit([dict(id=n.job.id, status=n.job.status, controller=n.job.controller_node, unit=n.job.work_unit_id, slice=n.job.job_slice_number)
      for n in wj.workflow_job_nodes.all() if n.job])
''',
        )
        return len(out) == 2 and all(x['status'] == 'running' and x['unit'] for x in out) and sorted(out, key=lambda x: x['slice'])

    sl = wait_for('both slices running', slices, 300, poll=3)
    s1 = sl[0]
    job_id, owner, unit = s1['id'], s1['controller'], s1['unit']
    oc, peer, ph = peer_of(containers, owner)
    m = {'workflow_job': wf, 'slices': sl, 'owner_slice_1': owner, 'branch': 'PR' if pr else 'devel', 'host_ids': original}
    notes = [f"job-slicing on {m['branch']}: slices {sl}"]
    arm_hold(peer, job_id, owner, args.seam_counter)
    arm_recorders(peer, None, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    orphan_owner(peer, ph, owner, job_id, args, m, pr)
    for x in sl:
        watch(peer, x['id'], x['unit'], args.finish_timeout, until=terminal, poll=10, label=f"slice {x['slice']} job")
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    ensure_up(containers)
    time.sleep(args.settle)
    per = orm(
        peer,
        f'''
from awx.main.models import Job
out = {{}}
for jid in {[x['id'] for x in sl]!r}:
    j = Job.objects.get(pk=jid)
    ev = sorted(set(j.get_event_queryset().exclude(host_name='').values_list('host_name', 'host_id')))
    su = sorted(j.job_host_summaries.values_list('host_name', 'host_id'))
    out[jid] = dict(slice=j.job_slice_number, status=j.status, controller=j.controller_node, event_hosts=ev, summaries=su)
emit(out)
''',
    )
    names = [{h for h, _ in v['event_hosts']} for v in per.values()]
    m['per_slice'] = per
    m['slices_disjoint'] = not (names[0] & names[1]) if len(names) == 2 else None
    m['slices_cover_inventory'] = (names[0] | names[1]) == set(original) if len(names) == 2 else None
    m['ids_original'] = all(original.get(h) == i for v in per.values() for h, i in v['event_hosts'] + v['summaries'])
    notes.append(f"per slice: {json.dumps(per, default=str)}")
    for jid, v in per.items():
        if int(jid) != job_id:
            report(containers, int(jid), since, args, None, (), out_name=f'{run_label(args)}-slice{v["slice"]}-job{jid}')
    m['adoptions'] = [
        f"{h['node']}@{h['at']} job={h['ctx'].get('job_id')} thr={h['ctx'].get('safe_threshold')}" for h in fired_hits(peer, 'adoption.after_snapshot')
    ]
    return report(containers, job_id, since, args, unit, notes, metrics=m, out_name=f'{run_label(args)}-slice1-job{job_id}')


def scenario_other_job_types(containers, args):
    """Other job types orphaned: --variant adhoc | project-update | inventory-update.

    The first results stream that opens on any controller is held (job.stream_started), so the
    job is caught after its work unit exists and before the controller reads it; that
    controller is killed and left down (PR: the peer is told at once). Then: adopted, reaped
    or stranded? adhoc runs a shell loop of --iterations seconds on receptor-1;
    project-update updates Demo Project; inventory-update runs a constructed inventory update.
    """
    need_two(containers, 'other-job-types')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    since = since_now()
    arm(c0, 'job.stream_started', 'pause', None, timeout=1800)
    if args.variant == 'adhoc':
        code = f'''
from awx.main.models import AdHocCommand, Inventory, Credential
inv = Inventory.objects.get(name='Demo Inventory')
cmd = AdHocCommand.objects.create(inventory=inv, credential=Credential.objects.get(name='Demo Credential'), module_name='shell',
    module_args='for i in $(seq 1 {args.iterations}); do echo tick $i; sleep 1; done', limit='all')
cmd.signal_start()
emit(cmd.id)
'''
    elif args.variant == 'project-update':
        code = "from awx.main.models import Project\npu = Project.objects.get(name='Demo Project').update()\nemit(pu.id)\n"
    else:
        code = '''
from awx.main.models import Inventory, Organization
org = Organization.objects.get(name='Default')
ci, _ = Inventory.objects.get_or_create(name='failpoint constructed', organization=org, kind='constructed')
demo = Inventory.objects.get(name='Demo Inventory')
if not ci.input_inventories.filter(pk=demo.pk).exists():
    ci.input_inventories.add(demo)
src = ci.inventory_sources.first()
if src is None:
    from awx.main.models import InventorySource
    src = InventorySource.objects.create(inventory=ci, name='failpoint constructed source', source='constructed', overwrite=True)
iu = src.update()
emit(iu.id)
'''
    job_id = orm(c0, code)
    log(f'launched {args.variant} {job_id}; the first results stream will hold')
    hit = wait_hits(c0, 'job.stream_started', timeout=300)[0]
    st = job_state(c0, job_id)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'job_type_id': job_id, 'owner': owner, 'execution_node': st['execution_node'], 'held': hit}
    notes = [f"other-job-types {args.variant} on {m['branch']}: {job_id} controller={owner} execution={st['execution_node']} unit={unit}"]
    if str(hit['ctx'].get('job_id')) != str(job_id):
        m['invalid'] = f"held stream belongs to {hit['ctx'].get('job_id')}, not {job_id}"
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    if args.variant == 'adhoc':
        time.sleep(args.lead)
    m['killed_at'] = kill(oc)
    manage(peer, 'failpoint', 'disarm', 'job.stream_started')
    if pr:
        force_lost(peer, ph, owner)
    return finish_and_report(containers, peer, job_id, unit, since, args, notes, m, pr)


def scenario_waiting_jobs(containers, args):
    """Waiting jobs: the controller dies holding jobs that have no work unit yet.

      --variant waiting       awx-1's dispatcher is frozen (SIGSTOP) and awx-2 disabled, so --orphans jobs
                              are assigned to awx-1 and stay 'waiting' (their start message is
                              never consumed); awx-2 is re-enabled and awx-1 killed
      --variant unit-unsaved  one job is held on awx-1 after its unit was submitted and before
                              work_unit_id is saved (job.after_submit_before_unit_saved); awx-1 is killed
    PR: awx-2 is told awx-1 is lost. Records what happens to each job and to the unit.
    """
    need_two(containers, 'waiting-jobs')
    c = 'tools_awx_2'
    pr = 'sweep.before_claim' in registry(c)
    manage(c, 'failpoint', 'disarm', '--all')
    manage(c, 'failpoint', 'clear-hits')
    since = since_now()
    m = {'variant': args.variant, 'branch': 'PR' if pr else 'devel'}
    notes = [f"waiting-jobs {args.variant} on {m['branch']}"]
    frozen = False
    jt = setup(containers, 'failpoint orphan', 'chatty.yml', {'iterations': args.iterations}, allow_simultaneous=True)
    units_before = set(json.loads(run(['docker', 'exec', EXEC_CONTAINER, 'receptorctl', '--socket', RECEPTOR_SOCK, 'work', 'list']).stdout or '{}'))
    set_instance(c, 'awx-2', enabled=False)
    wait_for('awx-2 capacity 0', lambda: instances(c)['awx-2']['capacity'] == 0, 180, poll=5)
    try:
        if args.variant == 'waiting':
            # SIGSTOP, not supervisorctl stop: a graceful stop runs dispatcherd's exit path, which
            # announces the shutdown and takes awx-1 out of capacity, so nothing would be placed there.
            run(['docker', 'exec', 'tools_awx_1', 'pkill', '-STOP', '-f', 'awx-manage dispatcherd'])
            frozen = True
            log("froze awx-1's dispatcher (SIGSTOP): start messages to awx-1 are never consumed")
            jobs = [launch(c, jt) for _ in range(args.orphans)]
            st = wait_for(
                f'{len(jobs)} jobs waiting on awx-1',
                lambda: (x := job_statuses(c, jobs)) and all(v['status'] == 'waiting' and v['controller'] == 'awx-1' for v in x.values()) and x,
                300,
                poll=5,
            )
        else:
            arm(c, 'job.after_submit_before_unit_saved', 'pause', {'node': 'awx-1'}, timeout=1800)
            jobs = [launch(c, jt)]
            wait_hits(c, 'job.after_submit_before_unit_saved', timeout=300)
            st = job_statuses(c, jobs)
            m['held_job_unit_id'] = job_state(c, jobs[0])['work_unit_id']
    except BaseException:
        if args.variant == 'waiting':
            run(['docker', 'exec', 'tools_awx_1', 'pkill', '-CONT', '-f', 'awx-manage dispatcherd'], check=False)
        raise
    finally:
        set_instance(c, 'awx-2', enabled=True)
    m['jobs'] = jobs
    m['before_kill'] = {j: (v['status'], v['controller']) for j, v in st.items()}
    wait_for('awx-2 capacity back', lambda: instances(c)['awx-2']['capacity'] > 0, 180, poll=5)
    m['killed_at'] = kill('tools_awx_1')
    m['dispatcher_frozen_until_kill'] = frozen
    manage(c, 'failpoint', 'disarm', '--all')
    if pr:
        force_lost(c, 'awx-2', 'awx-1')

    def done():
        x = job_statuses(c, jobs)
        return all(v['status'] not in ('pending', 'waiting', 'running') for v in x.values()) and x

    try:
        fin = wait_for('every job terminal', done, args.finish_timeout, poll=10)
    except TimeoutError as exc:
        notes.append(str(exc))
        fin = job_statuses(c, jobs)
    if pr:
        manage(c, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    units_after = json.loads(run(['docker', 'exec', EXEC_CONTAINER, 'receptorctl', '--socket', RECEPTOR_SOCK, 'work', 'list']).stdout or '{}')
    new_units = {u: v.get('StateName') for u, v in units_after.items() if u not in units_before}
    m['final'] = {j: dict(status=v['status'], controller=v['controller'], explanation=v['explanation']) for j, v in fin.items()}
    m['new_units_on_receptor_1'] = new_units
    m['playbooks_still_running'] = len(exec_node_processes(r'ansible-playbook'))
    start_back('tools_awx_1', 'awx-1')
    wait_for('execution node playbooks to drain', lambda: not exec_node_processes(r'ansible-playbook') or None, args.finish_timeout, poll=15)
    time.sleep(args.settle)
    notes.append(f"final: {m['final']}; new units on receptor-1: {new_units}")
    return report(containers, jobs[0], since, args, job_state(c, jobs[0])['work_unit_id'], notes, metrics=m)


def scenario_repeated_restarts(containers, args):
    """Repeated restarts: the controller is killed and restarted --restarts times during one job,
    each time held before an event counter (--seam-counter, then +--restart-step each time) so
    every restart lands at a known point. PR: peer claims are vetoed so every adoption is the
    owner's own. Do duplicates or gaps accumulate across the snapshots?"""
    need_two(containers, 'repeated-restarts')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'branch': 'PR' if pr else 'devel', 'restarts': args.restarts, 'snapshots': []}
    notes = [f"repeated-restarts x{args.restarts} on {m['branch']}"]
    arm_hold(peer, job_id, owner, args.seam_counter)
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    if pr:
        guard_peer(peer, job_id)
    for k in range(args.restarts):
        counter = args.seam_counter + k * args.restart_step
        if k:
            arm_hold(peer, job_id, owner, counter)
        wait_hold(peer, job_id, owner, counter)
        wait_db_events(peer, job_id, counter)
        n = len(fired_hits(peer, 'adoption.after_snapshot'))
        t = time.monotonic()
        kill_and_restart(oc, peer, owner)
        manage(peer, 'failpoint', 'disarm', 'callback.event')
        snap = wait_for(
            f'adoption {k + 1}', lambda n=n: (h := fired_hits(peer, 'adoption.after_snapshot')) and len(h) > n and h[-1], args.claim_timeout, poll=3
        )
        m['snapshots'].append(
            {
                'restart': k + 1,
                'held_before': counter,
                'node': snap['node'],
                'threshold': snap['ctx'].get('safe_threshold'),
                'kill_to_snapshot_s': round(time.monotonic() - t, 1),
            }
        )
        log(f"restart {k + 1}: adoption on {snap['node']} with threshold {snap['ctx'].get('safe_threshold')}")
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']}")
    m['unit_end'] = unit_end(peer, job_id, unit)
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_large_replay(containers, args):
    """Large replay: a job of --events fast events (bulk.yml) orphaned near the end of its burst.

      --variant peer     (PR) the owner is killed and left down; the peer adopts cross-node
      --variant restart  the owner is killed and restarted; it re-adopts its own job (both branches)
    The owner is held before event --events * 0.9. Samples the adopting worker's RSS every 2 s and
    times claim -> snapshot (the dedup query) and snapshot -> finalize (the replay).
    """
    need_two(containers, 'large-replay')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    if args.variant == 'peer' and not pr:
        raise SystemExit('large-replay --variant peer needs the PR branch')
    since = since_now()
    job_id, st = start_job(containers, args, jt_name='failpoint bulk', playbook='bulk.yml', extra_vars={'count': args.events})
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    hold = int(args.events * 0.9)
    m = {'owner': owner, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'count': args.events, 'held_before': hold}
    notes = [f"large-replay {args.variant} on {m['branch']}: {args.events} burst events"]
    arm_hold(peer, job_id, owner, hold)
    arm_recorders(peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release', 'adoption.before_finalize'])
    if pr and args.variant == 'restart':
        guard_peer(peer, job_id)
    t0 = time.monotonic()
    wait_for(f'job to reach event {hold}', lambda: pause_hits(peer, 'callback.event') or None, args.finish_timeout, poll=10)
    m['launch_to_hold_s'] = round(time.monotonic() - t0, 1)
    wait_db_events(peer, job_id, hold)
    m['events_at_kill'] = job_state(peer, job_id)['events']
    adopter, ac = (ph, peer) if args.variant == 'peer' else (owner, oc)
    if args.variant == 'peer':
        m['killed_at'] = kill(oc)
        manage(peer, 'failpoint', 'disarm', 'callback.event')
        force_lost(peer, ph, owner)
    else:
        m['killed_at'] = utcnow()
        kill_and_restart(oc, peer, owner)
        manage(peer, 'failpoint', 'disarm', 'callback.event')
    claim = wait_for('the adoption to claim', lambda: (h := fired_hits(peer, 'adoption.after_claim')) and h[0], args.claim_timeout, poll=1)
    pid = claim['pid']
    rss = []
    stop = threading.Event()

    def sampler():
        while not stop.is_set():
            out = run(['docker', 'exec', ac, 'ps', '-o', 'rss=', '-p', str(pid)], check=False).stdout.strip()
            if out:
                rss.append((utcnow(), int(out)))
            stop.wait(2)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=5)
    stop.set()
    th.join()
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    snap = fired_hits(peer, 'adoption.after_snapshot')
    fin = fired_hits(peer, 'adoption.before_finalize')
    m['adopter'] = adopter
    m['claim_at'] = claim['at']
    if snap:
        m['claim_to_snapshot_s'] = round(at_seconds(snap[0]['at']) - at_seconds(claim['at']), 2)
        m['safe_threshold'] = snap[0]['ctx'].get('safe_threshold')
    if snap and fin:
        m['snapshot_to_stream_end_s'] = round(at_seconds(fin[0]['at']) - at_seconds(snap[0]['at']), 1)
    m['rss_kb_peak'] = max((r for _, r in rss), default=None)
    m['rss_kb_first'] = rss[0][1] if rss else None
    m['rss_samples'] = len(rss)
    ensure_up(containers)
    time.sleep(args.settle)
    notes.append(f"job terminal: status={s['status']}; adopter {adopter} RSS {m['rss_kb_first']} -> peak {m['rss_kb_peak']} kB")
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_deprovision(containers, args):
    """Deprovision: awx-manage deprovision_instance on a controller that is alive and running a job.

    The owner is held before event --seam-counter (so the deprovision lands at a known point),
    deprovisioned from the peer, and released. PR: the peer's heartbeat is triggered (its sweep
    sees a job whose controller is no longer an instance). The owner is restarted afterwards so
    its bootstrap registers it again.
    """
    need_two(containers, 'deprovision')
    c0 = containers[0]
    pr = 'sweep.before_claim' in registry(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'branch': 'PR' if pr else 'devel'}
    notes = [f"deprovision on {m['branch']}: owner {owner}"]
    arm_hold(peer, job_id, owner, args.seam_counter)
    arm_recorders(
        peer, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'job.after_finalize_before_release', 'adoption.after_finalize_before_release']
    )
    wait_hold(peer, job_id, owner, args.seam_counter)
    out = manage(peer, 'deprovision_instance', f'--hostname={owner}', check=False)
    m['deprovisioned_at'] = utcnow()
    m['deprovision_output'] = (out.stdout + out.stderr).strip()[-300:]
    log(f'deprovisioned {owner}: {m["deprovision_output"]}')
    manage(peer, 'failpoint', 'disarm', 'callback.event')
    if pr:
        log(f'triggering a heartbeat on {ph} ({trigger_heartbeat(peer)})')
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    m['owner_instance_after'] = orm(peer, f'from awx.main.models import Instance\nemit(Instance.objects.filter(hostname={owner!r}).exists())\n')
    time.sleep(args.settle)
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in fired_hits(peer, 'adoption.after_snapshot')]
    m['finalizers'] = by_node(fired_hits(peer, 'job.after_finalize_before_release')) | {
        f'{k} (adoption)': v for k, v in by_node(fired_hits(peer, 'adoption.after_finalize_before_release')).items()
    }
    result = report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})
    run(['docker', 'restart', oc])
    log(f'restarted {oc} so its bootstrap registers {owner} again')
    wait_for(f'{owner} registered and ready', lambda: instances(peer).get(owner, {}).get('state') == 'ready', 600, poll=10)
    return result


# --- data correctness: host metrics, host pointers, stdout, notifications, activity stream ---

DC_INV = 'failpoint dc'
DC_CINV = 'failpoint dc constructed'
DC_HOSTS = ['dc-h1', 'dc-h2', 'dc-h3']
DC_NT = 'failpoint dc sink'
SINK = 'fp-sink'
SINK_URL = f'http://{SINK}:8080/'
SINK_IMAGE = 'ghcr.io/ansible/awx_devel:devel'
# A webhook sink: prints one JSON line per POST (UTC time, sender address, body) to its log.
SINK_CODE = r'''
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length') or 0)).decode('utf-8', 'replace')
        at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        print(json.dumps({'at': at, 'peer': self.client_address[0], 'path': self.path, 'body': body}), flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, *args):
        pass


HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
'''


def branch_tag(container):
    return 'pr' if is_pr_branch(container) else 'devel'


def sink_start():
    """Start the webhook sink container (once; later runs reuse it). Stop it with sink_stop()."""
    if run(['docker', 'ps', '-q', '-f', f'name=^{SINK}$']).stdout.strip():
        return
    run(['docker', 'rm', '-f', SINK], check=False)
    run(
        [
            'docker', 'run', '-d', '--rm', '--name', SINK, '--network', 'awx', '--cgroup-parent', 'awx-failpoints.slice',
            '--entrypoint', '/usr/bin/python3', SINK_IMAGE, '-u', '-c', SINK_CODE,
        ]
    )  # fmt: skip
    log(f'webhook sink {SINK} started ({SINK_URL})')


def sink_stop():
    run(['docker', 'rm', '-f', SINK], check=False)
    log(f'webhook sink {SINK} removed')


def container_ips(containers):
    """{ip on the awx network: hostname}, to tell which node posted a notification."""
    out = {}
    for c in containers:
        ip = run(['docker', 'inspect', c, '--format', '{{(index .NetworkSettings.Networks "awx").IPAddress}}'], check=False).stdout.strip()
        if ip:
            out[ip] = container_for_host(c)
    return out


def sink_posts(job_id, ips):
    """Every POST the sink received for this job: time, sending node, status, hosts."""
    out = run(['docker', 'logs', SINK], check=False).stdout
    posts = []
    for line in out.splitlines():
        try:
            rec = json.loads(line)
            body = json.loads(rec['body'])
        except ValueError:
            continue
        if not isinstance(body, dict) or body.get('id') != job_id:
            continue
        posts.append({'at': rec['at'], 'node': ips.get(rec['peer'], rec['peer']), 'status': body.get('status'), 'hosts': body.get('hosts')})
    return posts


def dc_inventory(container, constructed=False):
    """The 3-host inventory (created once, ids kept across runs), and optionally a constructed
    inventory over it, updated until it has the same 3 hosts. Returns names and ids."""
    info = orm(
        container,
        f'''
from awx.main.models import Inventory, Organization, Host, InventorySource
org = Organization.objects.get(name='Default')
inv, _ = Inventory.objects.get_or_create(name={DC_INV!r}, organization=org)
for n in {DC_HOSTS!r}:
    Host.objects.get_or_create(name=n, inventory=inv, defaults=dict(variables='ansible_connection: local', enabled=True))
out = dict(inv=inv.id, hosts={{h.name: h.id for h in inv.hosts.all()}}, update=None)
if {constructed!r}:
    ci, _ = Inventory.objects.get_or_create(name={DC_CINV!r}, organization=org, kind='constructed')
    if not ci.input_inventories.filter(pk=inv.pk).exists():
        ci.input_inventories.add(inv)
    src = ci.inventory_sources.first()
    if src is None:
        src = InventorySource.objects.create(inventory=ci, name='failpoint dc constructed source', source='constructed', overwrite=True)
    if ci.hosts.count() != {len(DC_HOSTS)}:
        out['update'] = src.update().id
    out['cinv'] = ci.id
emit(out)
''',
    )
    if info.get('update'):
        log(f"constructed inventory update {info['update']} launched")
        wait_for('constructed inventory update', lambda: terminal(job_state(container, info['update'])), 300, poll=5)
    if constructed:
        info['constructed_hosts'] = orm(
            container,
            f'''
from awx.main.models import Inventory
ci = Inventory.objects.get(name={DC_CINV!r})
emit({{h.name: dict(id=h.id, instance_id=h.instance_id) for h in ci.hosts.all()}})
''',
        )
        if len(info['constructed_hosts']) != len(DC_HOSTS):
            raise SystemExit(f"constructed inventory has {info['constructed_hosts']}, expected {DC_HOSTS}")
    return info


def dc_template(containers, args):
    """Template over the dc inventory (or its constructed inventory): datacheck.yml, forks=1,
    notifications to the sink only (not the port-9 webhook)."""
    constructed = bool(getattr(args, 'constructed', False))
    name = 'failpoint dc constructed' if constructed else 'failpoint dc'
    extra = {'iterations': args.iterations, 'fail_host': args.fail_host or ''}
    jt = setup(containers, name, 'datacheck.yml', extra, inventory=DC_CINV if constructed else DC_INV, jt_fields={'forks': 1})
    orm(
        containers[0],
        f'''
from awx.main.models import JobTemplate, NotificationTemplate, Organization
org = Organization.objects.get(name='Default')
jt = JobTemplate.objects.get(pk={jt})
nt, _ = NotificationTemplate.objects.get_or_create(name={DC_NT!r}, organization=org, notification_type='webhook',
    defaults=dict(notification_configuration={{'url': {SINK_URL!r}, 'headers': {{}}, 'http_method': 'POST',
        'disable_ssl_verification': True, 'username': '', 'password': ''}}))
for rel in (jt.notification_templates_success, jt.notification_templates_error, jt.notification_templates_started):
    rel.clear()
jt.notification_templates_success.add(nt)
jt.notification_templates_error.add(nt)
emit(jt.id)
''',
    )
    return jt


def dc_launch(container, jt_id):
    """Create the job, snapshot its hosts' HostMetric counters (for host_metrics_counted_once)
    and their pointers before the job, then start it."""
    return orm(
        container,
        f'''
from awx.main.models import JobTemplate, HostMetric
from awx.main.utils import failpoints
job = JobTemplate.objects.get(pk={jt_id}).create_unified_job()
names = sorted(h.name.lower() for h in job.inventory.hosts.all())
counters = dict(HostMetric.objects.filter(hostname__in=names).values_list('hostname', 'automated_counter'))
failpoints.record_snapshot('host_metrics', job.id, {{n: counters.get(n) for n in names}})
job.signal_start()
emit(job.id)
''',
    )


def dc_collect(container, job_id):
    """Everything the data-correctness scenarios compare, read from the DB."""
    return orm(
        container,
        f'''
from datetime import timedelta
from django.db.models import OuterRef, Subquery
from awx.main.models import ActivityStream, Host, HostMetric, Inventory, Job, JobHostSummary
from awx.main.utils.failpoints import get_snapshot
j = Job.objects.get(pk={job_id})
inv = j.inventory
summ = list(j.job_host_summaries.order_by('host_name').values('id', 'host_name', 'host_id', 'constructed_host_id', 'ok', 'changed',
    'failures', 'dark', 'processed', 'skipped', 'rescued', 'ignored', 'failed', 'created'))
def pointers(hosts):
    out = {{}}
    for h in hosts:
        s = JobHostSummary.objects.filter(host_id=h.id).order_by('-id').first()
        out[h.name + '#' + str(h.id)] = dict(last_job=s.job_id if s else None, last_job_host_summary=s.id if s else None,
                                             has_active_failures=bool(s and s.failed))
    return out
def computed(i):
    i.refresh_from_db()
    latest = JobHostSummary.objects.filter(host_id=OuterRef('pk')).order_by('-id').values('failed')[:1]
    failed = i.hosts.annotate(_f=Subquery(latest)).filter(_f=True).count()
    return dict(stored=dict(total_hosts=i.total_hosts, hosts_with_active_failures=i.hosts_with_active_failures,
                            has_active_failures=i.has_active_failures),
                computed=dict(total_hosts=i.hosts.count(), hosts_with_active_failures=failed, has_active_failures=bool(failed)))
inventories = {{inv.name: computed(inv)}}
originals = []
if inv.kind == 'constructed':
    originals = Host.objects.filter(pk__in=[int(x) for x in inv.hosts.values_list('instance_id', flat=True) if x])
    for src in inv.input_inventories.all():
        inventories[src.name] = computed(src)
names = sorted(h.name.lower() for h in inv.hosts.all())
qs = j.get_event_queryset()
def body(n):
    try:
        b = json.loads(n.body) if isinstance(n.body, str) else n.body
    except ValueError:
        b = None
    return b if isinstance(b, dict) else {{}}
notes = [dict(id=n.id, template=n.notification_template.name, created=n.created, delivery=n.status,
              status=body(n).get('status'), hosts=body(n).get('hosts')) for n in j.notifications.all().order_by('id')]
host_ids = set(inv.hosts.values_list('id', flat=True)) | set(h.id for h in originals)
since = j.created - timedelta(seconds=2)
acts = []
for a in ActivityStream.objects.filter(timestamp__gte=since).order_by('id'):
    acts.append(dict(id=a.id, at=a.timestamp, node=a.action_node, op=a.operation, object1=a.object1, object2=a.object2,
                     actor=a.actor.username if a.actor else None,
                     job=list(a.job.values_list('id', flat=True)), host=list(a.host.values_list('id', flat=True)),
                     notification=list(a.notification.values_list('id', flat=True)),
                     instance=list(a.instance.values_list('hostname', flat=True)),
                     changes=(a.changes or '')[:400]))
emit(dict(
    status=j.status, explanation=j.job_explanation, controller=j.controller_node, started=j.started, finished=j.finished,
    inventory=inv.name, inventory_kind=inv.kind, host_status_counts=j.host_status_counts,
    summaries=summ,
    pointers=pointers(inv.hosts.all()), original_pointers=pointers(originals),
    inventories=inventories,
    host_metrics_before=get_snapshot('host_metrics', j.id),
    host_metrics={{m.hostname: dict(automated_counter=m.automated_counter, first_automation=m.first_automation,
        last_automation=m.last_automation, deleted=m.deleted, deleted_counter=m.deleted_counter)
        for m in HostMetric.objects.filter(hostname__in=names)}},
    event_hosts=sorted(set(qs.exclude(host_name='').values_list('host_name', 'host_id'))),
    stats_rows=list(qs.filter(event='playbook_on_stats').values_list('counter', 'created')),
    events=qs.count(), distinct_counters=qs.values('counter').distinct().count(),
    stdout=j.result_stdout_raw,
    notifications=notes,
    activity=acts,
    activity_for_job=[a['id'] for a in acts if {job_id} in a['job']],
    activity_for_hosts=[a['id'] for a in acts if host_ids & set(a['host'])],
))
''',
    )


HOST_STAT_FIELDS = ('failed', 'changed', 'dark', 'failures', 'ok', 'processed', 'skipped', 'rescued', 'ignored')


def body_vs_summaries(status, hosts, summaries, job_status):
    """Compare one notification body (status, hosts) with the job's final status and summaries."""
    summ = {s['host_name']: s for s in summaries}
    hosts = hosts or {}
    bad = sorted(h for h in set(hosts) | set(summ) if h not in hosts or h not in summ or any(hosts[h].get(k) != summ[h][k] for k in HOST_STAT_FIELDS))
    return {
        'status': status,
        'status_matches_job': status == job_status,
        'hosts_in_body': len(hosts),
        'hosts_match_summaries': not bad,
        'mismatched_hosts': bad,
    }


def dc_summarize(d, posts):
    """The per-run numbers the write-up tables use."""
    before = d['host_metrics_before'] or {}
    counted = {s['host_name'].lower() for s in d['summaries'] if not s['dark']}
    deltas = {h: (d['host_metrics'].get(h, {}).get('automated_counter') or 0) - (before.get(h) or 0) for h in sorted(before)}
    last_jobs = {k: v['last_job'] for k, v in d['pointers'].items()}
    acts = d['activity']
    by_kind = Counter(f"{a['object1']}:{a['op']}" for a in acts)
    return {
        'status': d['status'],
        'summaries': len(d['summaries']),
        'summary_failed': sorted(s['host_name'] for s in d['summaries'] if s['failed']),
        'stats_rows': len(d['stats_rows']),
        'metric_deltas': deltas,
        'metrics_counted_once': all(deltas.get(h) == (1 if h in counted else 0) for h in deltas) if before else None,
        'last_job': last_jobs,
        'last_job_is_this': sorted({v for v in last_jobs.values()}),
        'has_active_failures': {k: v['has_active_failures'] for k, v in d['pointers'].items()},
        'original_last_job': {k: v['last_job'] for k, v in d['original_pointers'].items()},
        'inventories': d['inventories'],
        'inventory_fields_ok': all(v['stored'] == v['computed'] for v in d['inventories'].values()),
        'stdout_lines': d['stdout'].count('\n'),
        'notifications_db': [
            dict(id=n['id'], delivery=n['delivery'], **body_vs_summaries(n['status'], n['hosts'], d['summaries'], d['status'])) for n in d['notifications']
        ],
        'notifications_sink': [dict(at=p['at'], node=p['node'], **body_vs_summaries(p['status'], p['hosts'], d['summaries'], d['status'])) for p in posts],
        'activity_total': len(acts),
        'activity_by_kind': dict(by_kind),
        'activity_job_entries': [(a['op'], a['node'], a['changes'][:160]) for a in acts if a['id'] in d['activity_for_job']],
        'activity_host_entries': len(d['activity_for_hosts']),
    }


def dc_write(args, label, d, posts, summary):
    if not args.out:
        return
    out_dir = os.path.join(args.out, label)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'stdout.txt'), 'w') as fh:
        fh.write(d['stdout'])
    with open(os.path.join(out_dir, 'dc.json'), 'w') as fh:
        json.dump({k: v for k, v in d.items() if k != 'stdout'} | {'sink_posts': posts, 'summary': summary}, fh, indent=2, default=str)


def dc_start(containers, args):
    """Reset failpoints, launch a dc job and wait until it runs remotely with a work unit."""
    c0 = containers[0]
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    inv = dc_inventory(c0, constructed=bool(args.constructed))
    jt = dc_template(containers, args)
    job_id = dc_launch(c0, jt)
    log(
        f"launched job {job_id} (datacheck.yml, iterations={args.iterations}, fail_host={args.fail_host or '-'}, inventory={DC_CINV if args.constructed else DC_INV})"
    )
    st = wait_for('job running with a work unit', lambda: (s := job_state(c0, job_id))['status'] == 'running' and s['work_unit_id'] and s, 300)
    log(f"job {job_id} running: controller={st['controller_node']} execution={st['execution_node']} unit={st['work_unit_id']}")
    return job_id, st, inv


def slow_seam(c0, peer, ph, owner, job_id, args, m, notes, on_both_streaming=None):
    """slow-controller's seam drive, PR only: the owner is held before --seam-counter, its periodic
    heartbeat paused, the peer told it is lost (claim + second stream), then the owner is let go.
    The second finalizer of --order waits at callback.artifacts until the first has finalized.
    on_both_streaming() runs once both streams are live (stats-insert-race holds its writers there)."""
    second = owner if args.order == 'adopter-first' else ph
    arm(c0, 'callback.artifacts', 'pause', {'job_id': job_id, 'node': second}, timeout=1800)
    hold_at_counter(c0, job_id, owner, args.seam_counter)
    wait_db_events(c0, job_id, args.seam_counter)
    manage(c0, 'failpoint', 'arm', 'heartbeat.start', '--action', 'pause', '--match', f'node={owner}', '--match', 'periodic=True', '--timeout', '1200')
    hb = json.loads(manage(c0, 'failpoint', 'wait', 'heartbeat.start', '--timeout', '120').stdout)
    m['heartbeat_paused_at'] = hb['at']
    try:
        arm(c0, 'heartbeat.force_lost', 'trigger', {'node': ph, 'other': owner})
        log(f'seam: {ph} treats {owner} as lost; triggering its heartbeat ({trigger_heartbeat(peer)})')
        snap = wait_hits(c0, 'adoption.after_snapshot', timeout=args.claim_timeout, desc='the peer to claim and snapshot')[0]
        m['claim_node'], m['safe_threshold'] = snap['node'], int(snap['ctx']['safe_threshold'])
        manage(c0, 'failpoint', 'disarm', 'heartbeat.force_lost')
        manage(c0, 'failpoint', 'disarm', 'callback.event')
        log(f'seam: {snap["node"]} streams from threshold {m["safe_threshold"]}; released {owner} at counter {args.seam_counter}')
    finally:
        manage(peer, 'failpoint', 'release', 'heartbeat.start', check=False)
        manage(peer, 'failpoint', 'disarm', 'heartbeat.start', check=False)
    if on_both_streaming:
        on_both_streaming()
    first_hit = 'job.after_finalize_before_release' if second == ph else 'adoption.after_finalize_before_release'
    try:
        h = wait_hits(c0, first_hit, timeout=args.finish_timeout, poll=3)[0]
        log(f'seam: first finalizer done ({first_hit} on {h["node"]} at {h["at"]}); releasing {second}')
        m['first_finalizer'] = h['node']
    except TimeoutError as exc:
        notes.append(f'first finalizer never reached {first_hit}: {exc}')
    manage(c0, 'failpoint', 'disarm', 'callback.artifacts')


def slow_timing_devel(c0, peer, owner, job_id, args, m, notes):
    """devel has no claim: pause the owner's periodic heartbeat until the peer's lost path reaps
    the job (natural is_lost), then let the owner go on streaming and finalize it again."""
    manage(c0, 'failpoint', 'arm', 'heartbeat.start', '--action', 'pause', '--match', f'node={owner}', '--match', 'periodic=True', '--timeout', '1200')
    hb = json.loads(manage(c0, 'failpoint', 'wait', 'heartbeat.start', '--timeout', '120').stdout)
    m['heartbeat_paused_at'] = hb['at']
    try:
        s = wait_for('the peer to reap the job', lambda: (s := job_state(c0, job_id))['status'] != 'running' and s, args.claim_timeout, poll=5)
        m['reaped'] = {k: s[k] for k in ('status', 'job_explanation')}
        log(f'devel: job {job_id} now {m["reaped"]} while {owner} still streams')
    except TimeoutError as exc:
        notes.append(f'not reaped: {exc}')
    finally:
        manage(peer, 'failpoint', 'release', 'heartbeat.start', check=False)
        manage(peer, 'failpoint', 'disarm', 'heartbeat.start', check=False)


def scenario_data_check(containers, args):
    """Data correctness of an adopted job: host metrics, host pointers, inventory computed fields,
    stdout and its line ranges, notification bodies and the activity stream.

    datacheck.yml (forks=1, deterministic stdout) over the 3-host 'failpoint dc' inventory, or with
    --constructed over a constructed inventory of it. --fail-host NAME makes one host fail. The
    job notifies a webhook sink container (fp-sink) on success and failure.
      --variant normal      no fault (the reference)
      --variant same-node   owner held before --seam-counter, killed and restarted; it re-adopts
                            its own job (PR: peer claims vetoed)
      --variant cross-node  owner held and killed (left down until the end); PR: the peer adopts;
                            devel: the peer's lost path reaps after is_lost
      --variant slow        PR (--mode seam): slow-controller, both controllers stream and
                            finalize in --order; devel: the owner's heartbeat is paused until the
                            peer reaps, then the owner finalizes again
      --variant reap        a job that ends with no stats: PR, the peer's lost path claims and
                            adoption.before_queue raises once, so it reaps; devel: as cross-node
    Before launch the hosts' HostMetric counters are recorded as the host_metrics snapshot.
    Writes dc.json (all collected data) and stdout.txt next to result.json and metrics.json.
    """
    need_two(containers, 'data-check')
    c0 = containers[0]
    pr = is_pr_branch(c0)
    if args.variant == 'slow' and pr and args.mode != 'seam':
        raise SystemExit('data-check slow on the PR runs with --mode seam')
    sink_start()
    ips = container_ips(containers)
    since = since_now()
    job_id, st, inv = dc_start(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'fail_host': args.fail_host,
         'constructed': bool(args.constructed), 'inventory': inv}  # fmt: skip
    notes = [f"data-check {args.variant} on {m['branch']}: owner {owner}, peer {ph}"]
    arm_recorders(
        c0,
        job_id,
        [
            'adoption.after_claim',
            'adoption.after_snapshot',
            'job.after_finalize_before_release',
            'adoption.after_finalize_before_release',
            'events.stats_after_insert',
        ],
    )
    if args.variant == 'same-node':
        arm_hold(c0, job_id, owner, args.seam_counter)
        if pr:
            guard_peer(peer, job_id)
        wait_hold(c0, job_id, owner, args.seam_counter)
        wait_db_events(c0, job_id, args.seam_counter)
        m['killed_at'] = utcnow()
        kill_and_restart(oc, peer, owner)
        manage(peer, 'failpoint', 'disarm', 'callback.event')
    elif args.variant in ('cross-node', 'reap'):
        arm_hold(c0, job_id, owner, args.seam_counter)
        if args.variant == 'reap' and pr:
            arm(peer, 'adoption.before_queue', 'raise', {'job_id': job_id, 'node': ph}, times=1)
        orphan_owner(peer, ph, owner, job_id, args, m, pr)
    elif args.variant == 'slow':
        if pr:
            slow_seam(c0, peer, ph, owner, job_id, args, m, notes)
        else:
            slow_timing_devel(c0, peer, owner, job_id, args, m, notes)
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=5)
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']} explanation={s['job_explanation']!r}")
    m['unit_end'] = unit_end(peer, job_id, unit)
    if args.variant == 'slow' and not pr:
        # the owner's own stream ends after the reap; wait for its stats row
        wait_for('the owner to store playbook_on_stats', lambda: job_metrics(peer, job_id)['stats_rows'], args.finish_timeout, poll=10)
    ensure_up(containers)
    time.sleep(args.settle)
    m['adoptions'] = [f"{h['node']}@{h['at']} thr={h['ctx'].get('safe_threshold')}" for h in fired_hits(peer, 'adoption.after_snapshot')]
    m['stats_writers'] = [
        f"{h['node']}@{h['at']} new={h['ctx'].get('new')} metric_hosts={h['ctx'].get('metric_hosts')}" for h in fired_hits(peer, 'events.stats_after_insert')
    ]
    d = dc_collect(peer, job_id)
    posts = sink_posts(job_id, ips)
    summary = dc_summarize(d, posts)
    m['dc'] = summary
    label = f'{run_label(args)}-job{job_id}'
    result = report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})
    dc_write(args, label, d, posts, summary)
    return result


def synthetic_stats_race(containers, args, job_id, m):
    """Two awx-manage shells (one per control node) process the job's stored playbook_on_stats
    at the same instant, after its summaries are deleted: the code-level race without streams."""
    c0 = containers[0]
    n = orm(c0, f'from awx.main.models import JobHostSummary\nemit(JobHostSummary.objects.filter(job_id={job_id}).delete()[0])\n')
    before = orm(
        c0,
        f"from awx.main.models import HostMetric\nemit(dict(HostMetric.objects.filter(hostname__in={DC_HOSTS!r}).values_list('hostname', 'automated_counter')))\n",
    )
    m['synthetic'] = {'deleted_summaries': n, 'metrics_before': before}
    manage(c0, 'failpoint', 'clear-hits')
    arm(c0, 'events.stats_before_insert', 'pause', {'job_id': job_id}, timeout=600)
    arm(c0, 'events.stats_after_insert', 'sleep', {'job_id': job_id}, seconds=0)
    code = f'''
from awx.main.models import Job
from awx.main.utils.failpoints import get_snapshot
j = Job.objects.get(pk={job_id})
ev = j.get_event_queryset().filter(event='playbook_on_stats').order_by('counter').first()
ev.host_map = get_snapshot('host_map', j.id) or {{h.name: h.id for h in j.inventory.hosts.all()}}
try:
    ev._update_host_summary_from_stats(set(ev._hostnames()))
    emit('ok')
except Exception as exc:
    emit(f'{{type(exc).__name__}}: {{str(exc)[:300]}}')
'''
    results = {}

    def writer(c):
        try:
            results[c] = orm(c, code)
        except RuntimeError as exc:
            results[c] = f'shell failed: {str(exc)[-300:]}'

    threads = [threading.Thread(target=writer, args=(c,)) for c in containers]
    for t in threads:
        t.start()
    held = wait_hits(c0, 'events.stats_before_insert', lambda h: h['action'] == 'pause', count=len(containers), timeout=120)
    m['synthetic']['held'] = [f"{h['node']} pid={h['pid']} at={h['at']} existing={h['ctx'].get('existing')}" for h in held]
    if has_release_in(c0):
        rel = release_together(c0, ['events.stats_before_insert'])
        m['synthetic']['release'] = rel.get('at_utc')
        m['synthetic']['resumed'] = resumed(c0, ['events.stats_before_insert'])
    else:
        manage(c0, 'failpoint', 'release', 'events.stats_before_insert')
        m['synthetic']['release'] = utcnow() + ' (plain release: holders resume within one 0.25 s poll)'
    for t in threads:
        t.join(timeout=120)
    m['synthetic']['writers'] = results
    m['synthetic']['after_insert'] = [
        f"{h['node']} at={h['at']} new={h['ctx'].get('new')} metric_hosts={h['ctx'].get('metric_hosts')}" for h in fired_hits(c0, 'events.stats_after_insert')
    ]
    after = orm(
        c0,
        f"from awx.main.models import HostMetric\nemit(dict(HostMetric.objects.filter(hostname__in={DC_HOSTS!r}).values_list('hostname', 'automated_counter')))\n",
    )
    m['synthetic']['metric_deltas'] = {h: (after.get(h) or 0) - (before.get(h) or 0) for h in sorted(after)}
    m['synthetic']['summaries_after'] = orm(c0, f'from awx.main.models import JobHostSummary\nemit(JobHostSummary.objects.filter(job_id={job_id}).count())\n')
    manage(c0, 'failpoint', 'disarm', '--all')
    log(f"synthetic race: {json.dumps(m['synthetic'], default=str)}")


def has_release_in(container):
    return '--in' in manage(container, 'failpoint', 'release', '--help', check=False).stdout


def scenario_stats_insert_race(containers, args):
    """Two writers process the same playbook_on_stats at the same instant.

      --variant streams    (PR, --mode seam) slow-controller: the owner and the adopter both stream
                           the job, so each node's callback receiver processes its own copy of
                           playbook_on_stats. Both are held at events.stats_before_insert (after
                           reading the existing summaries, before the insert and the host metrics
                           update), then released at one scheduled instant.
      --variant synthetic  (both branches) a normal run, then its summaries are deleted and two
                           awx-manage shells, one per control node, re-process its stored stats
                           event, held and released the same way (devel: plain release).
    Measures: unique-constraint errors, aborted inserts, the summary count, the HostMetric
    automated_counter delta per host, and tracebacks.
    """
    need_two(containers, 'stats-insert-race')
    c0 = containers[0]
    pr = is_pr_branch(c0)
    if args.variant == 'streams' and not (pr and args.mode == 'seam'):
        raise SystemExit('stats-insert-race streams needs the PR branch and --mode seam')
    sink_start()
    ips = container_ips(containers)
    since = since_now()
    job_id, st, inv = dc_start(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'order': args.order}
    notes = [f"stats-insert-race {args.variant} on {m['branch']}"]
    arm_recorders(
        c0, job_id, ['adoption.after_snapshot', 'job.after_finalize_before_release', 'adoption.after_finalize_before_release', 'events.stats_after_insert']
    )
    if args.variant == 'streams':

        def hold_both_writers():
            held = wait_hits(c0, 'events.stats_before_insert', lambda h: h['action'] == 'pause', count=2, timeout=args.finish_timeout, poll=2)
            m['held'] = [f"{h['node']} pid={h['pid']} at={h['at']} new={h['ctx'].get('new')} existing={h['ctx'].get('existing')}" for h in held]
            m['held_nodes'] = sorted(h['node'] for h in held)
            log(f"both stats writers held: {m['held']}")
            rel = release_together(c0, ['events.stats_before_insert'])
            m['release_at'] = rel.get('at_utc')
            time.sleep(3)
            r = resumed(c0, ['events.stats_before_insert'])
            m['resumed'] = r
            wakes = [float(x['woke']) for x in r if x.get('woke')]
            m['resume_spread_ms'] = round((max(wakes) - min(wakes)) * 1000, 3) if len(wakes) > 1 else None

        arm(c0, 'events.stats_before_insert', 'pause', {'job_id': job_id}, timeout=1800)
        slow_seam(c0, peer, ph, owner, job_id, args, m, notes, on_both_streaming=hold_both_writers)
    s = watch(peer, job_id, unit, args.finish_timeout, until=terminal, poll=5)
    manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    m['unit_end'] = unit_end(peer, job_id, unit)
    ensure_up(containers)
    time.sleep(args.settle)
    m['stats_writers'] = [
        f"{h['node']}@{h['at']} new={h['ctx'].get('new')} metric_hosts={h['ctx'].get('metric_hosts')}" for h in fired_hits(c0, 'events.stats_after_insert')
    ]
    d = dc_collect(c0, job_id)
    posts = sink_posts(job_id, ips)
    m['dc'] = dc_summarize(d, posts)
    notes.append(f"job terminal: status={s['status']}; summaries={m['dc']['summaries']} metric deltas={m['dc']['metric_deltas']}")
    if args.variant == 'synthetic':
        synthetic_stats_race(containers, args, job_id, m)

    def from_logs(logs):
        pat = re.compile(r'IntegrityError|UniqueViolation|duplicate key value')
        hits = {container_for_host(c): sum(1 for line in lines if pat.search(line)) for c, lines in logs.items()}
        return {'unique_errors_in_logs': {k: v for k, v in hits.items() if v}, 'log_counts': count_log_lines(logs, job_id, unit)}

    label = f'{run_label(args)}-job{job_id}'
    result = report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=from_logs)
    dc_write(args, label, d, posts, m['dc'])
    return result


def scenario_dc_cleanup(containers, args):
    """Remove what data-check and stats-insert-race created: templates, the sink notification
    template, the constructed and plain dc inventories (and their hosts), the dc-* HostMetric
    rows, and the sink container."""
    out = orm(
        containers[0],
        f'''
from awx.main.models import HostMetric, Inventory, JobTemplate, NotificationTemplate
done = {{}}
done['templates'] = JobTemplate.objects.filter(name__in=['failpoint dc', 'failpoint dc constructed']).delete()[0]
done['notification_templates'] = NotificationTemplate.objects.filter(name={DC_NT!r}).delete()[0]
for name in ({DC_CINV!r}, {DC_INV!r}):
    for inv in Inventory.objects.filter(name=name):
        inv.hosts.all().delete()
        inv.delete()
        done[name] = 'deleted'
done['host_metrics'] = HostMetric.objects.filter(hostname__in={[h.lower() for h in DC_HOSTS]!r}).delete()[0]
emit(done)
''',
    )
    log(f'dc cleanup: {out}')
    sink_stop()
    return {'ok': True}


# --- job control and capacity, part 4 extras -------------------------------------------------

OVERLAP_MARKER = '/tmp/fp-overlap.log'
LOCAL_SETTINGS = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools', 'docker-compose', '_sources', 'local_settings.py')
AWX2_OVERRIDE_MARK = '# failpoint scenarios: awx-2 override (remove after the run)'


def unit_events(unit):
    """Per-host (first, last) event 'created' epoch from a work unit's raw stdout on receptor-1.
    The unit keeps the whole runner stream until it is released, also for a reaped job."""
    out = run(['docker', 'exec', EXEC_CONTAINER, 'sh', '-c', f'cat /tmp/receptor/*/{unit}/stdout 2>/dev/null'], check=False).stdout
    per = {}
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        host = (ev.get('event_data') or {}).get('host') if isinstance(ev, dict) else None
        if not host or not ev.get('created'):
            continue
        t = at_seconds(ev['created'] if ev['created'].endswith('Z') or '+' in ev['created'] else ev['created'] + '+00:00')
        lo, hi = per.get(host, (t, t))
        per[host] = (min(lo, t), max(hi, t))
    return per


def marker_ranges():
    """{job_id: {host: (first, last)}} from the shared marker file, if the playbooks could write it."""
    out = run(['docker', 'exec', EXEC_CONTAINER, 'cat', OVERLAP_MARKER], check=False).stdout
    per = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        job, host, _, t = parts
        lo, hi = per.setdefault(job, {}).get(host, (float(t), float(t)))
        per[job][host] = (min(lo, float(t)), max(hi, float(t)))
    return per


def db_host_ranges(container, job_id):
    return orm(
        container,
        f'''
from django.db.models import Min, Max
from awx.main.models import Job
j = Job.objects.get(pk={job_id})
emit({{r['host_name']: (r['lo'].timestamp(), r['hi'].timestamp()) for r in
      j.get_event_queryset().exclude(host_name='').values('host_name').annotate(lo=Min('created'), hi=Max('created'))}})
''',
    )


def overlaps(a, b):
    """Per host: seconds both ranges cover."""
    return {h: round(max(0.0, min(a[h][1], b[h][1]) - max(a[h][0], b[h][0])), 1) for h in sorted(set(a) & set(b))}


def scenario_same_hosts(containers, args):
    """Two playbooks on the same hosts: allow_simultaneous=False, the first job orphaned.

    overlap.yml (each loop item appends job id, host and time to a marker file on receptor-1,
    then sleeps 1 s) over the 3 dc hosts. Job A's owner is held before --seam-counter and killed
    (left down until the end). Job B, from the same template, is launched right after the kill.
      --variant kill  PR: the peer adopts A (seam); devel: the peer's lost path reaps A after is_lost
      --variant reap  PR: the peer claims A and adoption.before_queue raises once, so A is reaped
    Measures when B starts against when A's playbook really ends, and the per-host overlap of
    A's and B's playbook activity (marker file; else the work units' event times).
    """
    need_two(containers, 'same-hosts')
    c0 = containers[0]
    pr = is_pr_branch(c0)
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    run(['docker', 'exec', EXEC_CONTAINER, 'rm', '-f', OVERLAP_MARKER], check=False)
    dc_inventory(c0)
    jt = setup(containers, 'failpoint overlap', 'overlap.yml', {'iterations': args.iterations}, inventory=DC_INV, allow_simultaneous=False)
    since = since_now()
    a = launch(c0, jt)
    st = wait_for('job A running with a work unit', lambda: (s := job_state(c0, a))['status'] == 'running' and s['work_unit_id'] and s, 300)
    owner, unit_a = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel', 'job_a': a, 'unit_a': unit_a}
    notes = [f"same-hosts {args.variant} on {m['branch']}: A={a} owner {owner}"]
    arm_hold(c0, a, owner, args.seam_counter)
    arm_recorders(peer, a, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
    if args.variant == 'reap' and pr:
        arm(peer, 'adoption.before_queue', 'raise', {'job_id': a, 'node': ph}, times=1)
    wait_hold(c0, a, owner, args.seam_counter)
    wait_db_events(c0, a, args.seam_counter)
    m['killed_at'] = kill(oc)
    manage(peer, 'failpoint', 'disarm', 'callback.event')
    b = launch(peer, jt)
    m['job_b'] = b
    m['b_launched_at'] = utcnow()
    log(f'launched B = job {b} from the same template')
    if pr:
        force_lost(peer, ph, owner)

    def both():
        sa, sb = job_state(peer, a), job_state(peer, b)
        return {'A': (sa['status'], sa['controller_node']), 'B': (sb['status'], sb['controller_node'])}

    watch(peer, a, unit_a, args.finish_timeout, until=terminal, poll=5, label='A', extra=both)
    m['a_terminal_at'] = utcnow()
    sb = wait_for('B to start', lambda: (s := job_state(peer, b))['status'] not in ('pending', 'waiting') and s, args.finish_timeout, poll=3)
    m['b_running_at'] = utcnow()
    unit_b = sb['work_unit_id']
    m['unit_a_end'] = unit_end(peer, a, unit_a, seconds=args.finish_timeout)
    m['a_events_on_unit'] = unit_events(unit_a)
    watch(peer, b, unit_b, args.finish_timeout, until=terminal, poll=10, label='B')
    if pr:
        manage(peer, 'failpoint', 'disarm', 'heartbeat.force_lost', check=False)
    ensure_up(containers)
    time.sleep(args.settle)
    times = orm(
        peer,
        f'''
from awx.main.models import Job
out = {{}}
for jid in ({a}, {b}):
    j = Job.objects.get(pk=jid)
    out[jid] = dict(created=j.created, started=j.started, finished=j.finished, status=j.status, explanation=j.job_explanation, controller=j.controller_node)
emit(out)
''',
    )
    m['jobs'] = times
    m['b_wait_s'] = round(at_seconds(times[str(b)]['started']) - at_seconds(times[str(b)]['created']), 1) if times[str(b)]['started'] else None
    markers = marker_ranges()
    m['marker_file'] = bool(markers)
    if markers:
        ra, rb = markers.get(str(a), {}), markers.get(str(b), {})
    else:
        ra = m['a_events_on_unit'] or db_host_ranges(peer, a)
        rb = db_host_ranges(peer, b)
    m['a_ranges'], m['b_ranges'] = ra, rb
    m['overlap_s'] = overlaps(ra, rb)
    m['a_playbook_end'] = max((v[1] for v in ra.values()), default=None)
    m['b_playbook_start'] = min((v[0] for v in rb.values()), default=None)
    notes.append(f"A {times[str(a)]['status']}, B started {m['b_wait_s']}s after launch; per-host overlap {m['overlap_s']}")
    report(containers, b, since, args, unit_b, (), out_name=f'{run_label(args)}-B-job{b}')
    return report(containers, a, since, args, unit_a, notes, metrics=m, out_name=f'{run_label(args)}-A-job{a}')


def awx2_override(lines):
    """Append a guarded block to the shared local_settings.py that applies on awx-2 only.
    Returns the original text; restore it with awx2_restore()."""
    with open(LOCAL_SETTINGS) as fh:
        orig = fh.read()
    block = '\n' + AWX2_OVERRIDE_MARK + '\nif CLUSTER_HOST_ID == "awx-2":\n' + ''.join(f'    {line}\n' for line in lines)
    with open(LOCAL_SETTINGS, 'w') as fh:
        fh.write(orig + block)
    log(f'local_settings.py: awx-2 override {lines}')
    return orig


def awx2_restore(orig):
    with open(LOCAL_SETTINGS, 'w') as fh:
        fh.write(orig)
    log('local_settings.py restored')


def restart_workers(container):
    run(['docker', 'exec', container, 'supervisorctl', 'restart', 'tower-processes:awx-dispatcher', 'tower-processes:awx-receiver'])
    log(f'{container}: dispatcher and receiver restarted')


def pool_info(container):
    """Effective dispatcher pool: max_workers from the running config, and current workers."""
    cfg = orm(container, 'from awx.main.utils.common import get_auto_max_workers\nemit(get_auto_max_workers())\n')
    out = run(['docker', 'exec', container, 'dispatcherctl', 'status'], check=False).stdout
    mw = re.findall(r'max_workers\D+(\d+)', out)
    return {'get_auto_max_workers': cfg, 'status_max_workers': mw[:1], 'workers': dispatcher_workers(container)['workers']}


def status_only(container, job_ids):
    """{job id: status}."""
    return {k: v['status'] for k, v in _job_statuses(container, job_ids).items()}


def scenario_few_workers(containers, args):
    """Too few dispatcher workers on the adopter.

    The dispatcher has no max_workers setting: it uses get_auto_max_workers() =
    max(cpu capacity, memory capacity) + 7, from SYSTEM_TASK_ABS_CPU / SYSTEM_TASK_ABS_MEM (setting
    or env). Those same values size the node's capacity. awx-2 gets small values (local_settings.py,
    awx-2 only) so its pool is --workers-ish, then --orphans jobs placed on awx-1 are orphaned
    (awx-1 killed and left down; PR: awx-2 told at once). Samples awx-2's pool, its heartbeat
    (last_seen), job states and a probe job and project update launched after the kill.
    """
    need_two(containers, 'few-workers')
    c0, c2 = 'tools_awx_1', 'tools_awx_2'
    pr = is_pr_branch(c2)
    manage(c2, 'failpoint', 'disarm', '--all')
    manage(c2, 'failpoint', 'clear-hits')
    m = {'branch': 'PR' if pr else 'devel', 'orphans': args.orphans}
    notes = []
    orig = awx2_override([f"SYSTEM_TASK_ABS_CPU = '{args.abs_cpu}'", f"SYSTEM_TASK_ABS_MEM = '{args.abs_mem}'"])
    try:
        restart_workers(c2)
        wait_for('awx-2 heartbeat with new capacity', lambda: (i := instances(c2)['awx-2'])['capacity'] and i['capacity'] < 100 and i, 240, poll=10)
        m['awx2_before'] = instances(c2)['awx-2']
        m['pool_before'] = pool_info(c2)
        log(f"awx-2 now {m['awx2_before']}; pool {m['pool_before']}")
        set_instance(c2, 'awx-2', enabled=False)
        jt = setup(containers, 'failpoint chatty multi', 'chatty.yml', {'iterations': args.iterations}, allow_simultaneous=True)
        since = since_now()
        ids = orm(
            c0,
            f'''
from awx.main.models import JobTemplate
jt = JobTemplate.objects.get(pk={jt})
ids = []
for _ in range({args.orphans}):
    j = jt.create_unified_job()
    j.signal_start()
    ids.append(j.id)
emit(ids)
''',
        )
        m['jobs'] = ids
        wait_for('all orphans running on awx-1', lambda: all(s == 'running' for s in status_only(c0, ids).values()), 300, poll=5)
        set_instance(c2, 'awx-2', enabled=True)
        probe_jt = setup(containers, 'failpoint probe', 'chatty.yml', {'iterations': 3}, allow_simultaneous=True)
        arm_recorders(c2, None, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.after_finalize_before_release'])
        time.sleep(args.lead)
        m['killed_at'] = kill(c0)
        if pr:
            force_lost(c2, 'awx-2', 'awx-1')
        samples = []
        probes = {}
        t_kill = time.monotonic()

        def sample():
            st = orm(
                c2,
                f'''
from awx.main.models import UnifiedJob, Instance
from django.utils.timezone import now
emit(dict(at=now(), jobs={{j.id: (j.status, j.controller_node) for j in UnifiedJob.objects.filter(pk__in={ids!r})}},
          awx2_last_seen=Instance.objects.get(hostname='awx-2').last_seen, awx2_state=Instance.objects.get(hostname='awx-2').node_state,
          awx2_consumed=Instance.objects.get(hostname='awx-2').consumed_capacity, awx2_capacity=Instance.objects.get(hostname='awx-2').capacity))
''',
            )
            w = dispatcher_workers(c2)
            st['workers'] = w['workers']
            st['busy'] = w['busy']
            st['adoptions_running'] = w['adopt']
            st['tasks'] = w['tasks']
            st['by_status'] = dict(Counter(v[0] + '@' + (v[1] or '-') for v in st['jobs'].values()))
            del st['jobs']
            samples.append(st)
            log(f"sample: workers={st['workers']} busy={st['busy']} adopt={st['adoptions_running']} {st['by_status']} last_seen={st['awx2_last_seen']}")

        while time.monotonic() - t_kill < args.observe:
            sample()
            if not probes and time.monotonic() - t_kill > 30:
                probes['job'] = launch(c2, probe_jt)
                probes['project_update'] = orm(c2, "from awx.main.models import Project\nemit(Project.objects.get(name='Demo Project').update().id)\n")
                m['probes_launched_at'] = utcnow()
                log(f'probes launched: {probes}')
            if all(s not in ('pending', 'waiting', 'running') for s in status_only(c2, ids).values()):
                break
            time.sleep(args.sample)
        m['samples'] = samples
        m['probes'] = probes
        m['probe_times'] = orm(
            c2,
            f'''
from awx.main.models import UnifiedJob
emit({{j.id: dict(created=j.created, started=j.started, finished=j.finished, status=j.status, controller=j.controller_node)
      for j in UnifiedJob.objects.filter(pk__in={list(probes.values())!r})}})
''',
        )
        final = status_only(c2, ids)
        m['final'] = dict(Counter(final.values()))
        m['kill_to_all_terminal_s'] = round(time.monotonic() - t_kill, 1) if all(s not in ('pending', 'waiting', 'running') for s in final.values()) else None
        m['adoptions'] = by_node(fired_hits(c2, 'adoption.after_snapshot'))
        m['adoption_snapshots'] = sorted(h['at'] for h in fired_hits(c2, 'adoption.after_snapshot'))
        m['adoption_claims'] = sorted(h['at'] for h in fired_hits(c2, 'adoption.after_claim'))
    finally:
        awx2_restore(orig)
        restart_workers(c2)
        start_back(c0, 'awx-1')
        set_instance(c2, 'awx-2', enabled=True)
    wait_for('awx-2 capacity restored', lambda: instances(c2)['awx-2']['capacity'] > 100, 300, poll=10)
    m['pool_after'] = pool_info(c2)
    time.sleep(args.settle)

    def from_logs(logs):
        out = count_log_lines(logs, ids[0])
        pat = re.compile(r'max_workers|queue pressure|capacity may be insufficient|deferring|out of control capacity')
        out['pool_pressure_lines'] = {container_for_host(c): sum(1 for line in lines if pat.search(line)) for c, lines in logs.items()}
        return out

    return report(containers, ids[0], since, args, None, notes, metrics=m, from_logs=from_logs)


def scenario_disable_live(containers, args):
    """Disabling a live controller while it runs a job (it is not killed).

      --variant disable        enabled=False on the owner
      --variant deprovisioning node_state='deprovisioning' on the owner (the nearest thing to
                               draining in this version; written straight to the row)
    Watches --observe seconds (several of the peer's heartbeats; the peer's heartbeat is also
    triggered) for any claim, adoption, second stream, duplicate event or extra notification,
    then restores the owner and lets the job finish.
    """
    need_two(containers, 'disable-live')
    c0 = containers[0]
    pr = is_pr_branch(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc, peer, ph = peer_of(containers, owner)
    m = {'owner': owner, 'peer': ph, 'variant': args.variant, 'branch': 'PR' if pr else 'devel'}
    notes = [f"disable-live {args.variant} on {m['branch']}"]
    arm_recorders(c0, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'adoption.before_queue', 'sweep.before_claim', 'lost_instance.before_claim'])
    time.sleep(args.lead)
    if args.variant == 'disable':
        m['changed'] = set_instance(c0, owner, enabled=False)
    else:
        m['changed'] = set_instance(c0, owner, node_state='deprovisioning')
    m['changed_at'] = utcnow()
    try:
        for _ in range(3):
            time.sleep(args.observe / 3)
            if pr:
                trigger_heartbeat(peer)
            s = job_state(c0, job_id)
            log(f"observe: job {s['status']} controller={s['controller_node']} events={s['events']}; {owner}={instances(c0)[owner]}")
        m['during'] = {k: s[k] for k in ('status', 'controller_node', 'events')}
        m['owner_state_during'] = instances(c0)[owner]
    finally:
        if args.variant == 'disable':
            set_instance(c0, owner, enabled=True)
        else:
            set_instance(c0, owner, node_state='ready')
        m['restored_at'] = utcnow()
    m['claims'] = {
        name: by_node(fired_hits(c0, name)) for name in ('sweep.before_claim', 'lost_instance.before_claim', 'adoption.after_claim', 'adoption.after_snapshot')
    }
    s = watch(c0, job_id, unit, args.finish_timeout, until=terminal, poll=10)
    time.sleep(args.settle)
    notes.append(f"job terminal: status={s['status']} controller={s['controller_node']}")
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_capacity_race(containers, args):
    """Orphans and new launches competing for capacity.

    awx-2's cpu capacity is forced to 1 (SYSTEM_TASK_ABS_CPU='0.25', awx-2 only) and two long
    fillers are placed on it; capacity_adjustment=0 gives capacity 1, consumed 2. The scenario
    job O runs on awx-1, which is killed and left down (PR: awx-2 told at once; its lost path
    declines for lack of room, so O stays owned by the dead awx-1). --pending launches of a short
    template are queued; they cannot be placed either. Then capacity is freed:
      --variant free-one   cancel one filler: remaining capacity goes from -1 to 0
      --variant free-two   cancel both fillers: remaining capacity goes from -1 to 1
    Records who takes the freed capacity first (the sweep claiming O, or the task manager
    starting a pending launch), and what happens next, for --observe seconds.
    """
    need_two(containers, 'capacity-race')
    c0, c2 = 'tools_awx_1', 'tools_awx_2'
    pr = is_pr_branch(c2)
    manage(c2, 'failpoint', 'disarm', '--all')
    manage(c2, 'failpoint', 'clear-hits')
    m = {'branch': 'PR' if pr else 'devel', 'variant': args.variant, 'pending': args.pending}
    notes = []
    orig = awx2_override(["SYSTEM_TASK_ABS_CPU = '0.25'"])
    fillers, pend = [], []
    try:
        restart_workers(c2)
        time.sleep(15)
        set_instance(c2, 'awx-1', enabled=False)
        filler_jt = setup(containers, 'failpoint filler', 'quiet.yml', {'quiet_seconds': 1800}, allow_simultaneous=True)
        fillers = [launch(c2, filler_jt) for _ in range(2)]
        for f in fillers:
            wait_for(f'filler {f} running on awx-2', lambda f=f: (s := job_state(c2, f))['status'] == 'running' and s['controller_node'] == 'awx-2' and s, 300)
        set_instance(c2, 'awx-1', enabled=True)
        wait_for('awx-1 capacity back', lambda: instances(c2)['awx-1']['capacity'] > 0, 180, poll=5)
        since = since_now()
        job_id, st = start_job(containers, args, reset=False)
        unit = st['work_unit_id']
        if st['controller_node'] != 'awx-1':
            raise SystemExit(f"O went to {st['controller_node']}, expected awx-1")
        arm_recorders(c2, job_id, ['adoption.after_claim', 'adoption.after_snapshot', 'sweep.before_claim', 'lost_instance.before_claim'])
        set_instance(c2, 'awx-2', capacity_adjustment=0)
        m['awx2'] = wait_for('awx-2 capacity 1', lambda: (i := instances(c2))['awx-2']['capacity'] == 1 and i['awx-2'], 180, poll=5)
        pend_jt = setup(containers, 'failpoint pending', 'chatty.yml', {'iterations': 60}, allow_simultaneous=True)
        m['killed_at'] = kill(c0)
        if pr:
            force_lost(c2, 'awx-2', 'awx-1')
        wait_for('awx-1 marked lost', lambda: instances(c2)['awx-1']['state'] != 'ready' or None, 600, poll=10)
        time.sleep(20)
        m['o_before_free'] = job_state(c2, job_id)
        pend = [launch(c2, pend_jt) for _ in range(args.pending)]
        time.sleep(30)
        m['pending_before_free'] = _job_statuses(c2, pend)
        to_cancel = fillers[:1] if args.variant == 'free-one' else fillers
        cancel_at = utcnow()
        for f in to_cancel:
            cancel_job(c2, f)
        m['freed_at'] = cancel_at
        log(f'canceled fillers {to_cancel} at {cancel_at}')
        timeline = []
        t0 = time.monotonic()
        last = None
        while time.monotonic() - t0 < args.observe:
            o = job_state(c2, job_id)
            ps = orm(
                c2,
                f'''
from awx.main.models import UnifiedJob, Instance
i = Instance.objects.get(hostname='awx-2')
emit(dict(pending={{j.id: (j.status, j.controller_node, j.started) for j in UnifiedJob.objects.filter(pk__in={pend!r})}},
          capacity=i.capacity, consumed=i.consumed_capacity))
''',
            )
            snap = (o['status'], o['controller_node'], json.dumps({k: v[:2] for k, v in ps['pending'].items()}), ps['consumed'])
            if snap != last:
                row = {
                    't': round(time.monotonic() - t0, 1),
                    'at': utcnow(),
                    'O': (o['status'], o['controller_node']),
                    'pending': ps['pending'],
                    'consumed': ps['consumed'],
                    'capacity': ps['capacity'],
                }
                timeline.append(row)
                log(f'after free: {row}')
                last = snap
            if terminal(o) and all(v[0] not in ('pending', 'waiting') for v in ps['pending'].values()):
                break
            time.sleep(3)
        m['timeline'] = timeline
        snaps = fired_hits(c2, 'adoption.after_snapshot')
        m['o_adopted_at'] = snaps[0]['at'] if snaps else None
        claims = fired_hits(c2, 'adoption.after_claim')
        m['o_claimed_at'] = claims[0]['at'] if claims else None
        m['o_claim_attempts'] = [f"{h['node']}@{h['at']}" for h in fired_hits(c2, 'sweep.before_claim') + fired_hits(c2, 'lost_instance.before_claim')]
        m['o_adoption_tasks'] = len(claims)
        starts = orm(
            c2,
            f'''
from awx.main.models import UnifiedJob
emit({{j.id: dict(started=j.started, status=j.status, controller=j.controller_node) for j in UnifiedJob.objects.filter(pk__in={pend!r})}})
''',
        )
        m['pending_starts'] = starts
        first_launch = min((at_seconds(v['started']) for v in starts.values() if v['started']), default=None)
        m['first_launch_started'] = first_launch
        first_claim = at_seconds(claims[0]['at']) if claims else None
        if first_claim is not None and (first_launch is None or first_claim < first_launch):
            m['winner'] = 'orphan claimed first' + ('' if snaps else ', never streamed while observed')
        elif first_launch is not None:
            m['winner'] = 'launch started first'
        else:
            m['winner'] = 'none'
        s = watch(c2, job_id, unit, args.finish_timeout, until=terminal, poll=10)
        notes.append(f"O terminal: {s['status']} controller={s['controller_node']}; winner of the freed capacity: {m['winner']}")
    finally:
        for j in fillers + pend:
            try:
                cancel_job(c2, j)
            except RuntimeError:
                pass
        set_instance(c2, 'awx-2', capacity_adjustment=1)
        awx2_restore(orig)
        restart_workers(c2)
        start_back(c0, 'awx-1')
        set_instance(c2, 'awx-1', enabled=True)
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes, metrics=m, from_logs=lambda logs: {'log_counts': count_log_lines(logs, job_id, unit)})


def scenario_report(containers, args):
    """Report only: invariants, timeline and saved logs for --job since --since (a run cut short)."""
    if not (args.job and args.since):
        raise SystemExit('report needs --job and --since')
    alive = [c for c in containers if manage(c, 'failpoint', 'list', check=False).returncode == 0]
    unit = job_state(alive[0], args.job)['work_unit_id']
    return report(containers, args.job, args.since, args, unit, args.note or ())


VARIANTS = {
    'cancel-orphan': ('dead', 'restart', 'task-id-window', 'deferred'),
    'adopter-dies': ('third', 'return'),
    'claim-race': ('sweep-sweep', 'lost-sweep', 'lost-lost', 'lost-then-sweep'),
    'workflow-orphan': ('slow', 'kill'),
    'set-stats-artifacts': ('kill', 'slow'),
    'claim-no-queue': ('lost', 'sweep', 'after-publish'),
    'both-controllers-lost': ('peer-returns', 'owner-returns'),
    'exec-node-dies': ('restart', 'kill-start'),
    'job-timeout': ('kill', 'none'),
    'fact-cache': ('kill', 'none'),
    'other-job-types': ('adhoc', 'project-update', 'inventory-update'),
    'waiting-jobs': ('waiting', 'unit-unsaved'),
    'large-replay': ('peer', 'restart'),
    'data-check': ('normal', 'same-node', 'cross-node', 'slow', 'reap'),
    'stats-insert-race': ('streams', 'synthetic'),
    'same-hosts': ('kill', 'reap'),
    'disable-live': ('disable', 'deprovisioning'),
    'capacity-race': ('free-one', 'free-two'),
}

SCENARIOS = {
    'slow-controller': scenario_slow_controller,
    'finalize-strand': scenario_finalize_strand,
    'quiet-deadline': scenario_quiet_deadline,
    'self-unavailable': scenario_self_unavailable,
    'cancel-orphan': scenario_cancel_orphan,
    'capacity-strand': scenario_capacity_strand,
    'capacity-disabled': scenario_capacity_disabled,
    'hybrid-resume': scenario_hybrid_resume,
    'event-queue': scenario_event_queue,
    'host-map': scenario_host_map,
    'log-rotation': scenario_log_rotation,
    'adopter-dies': scenario_adopter_dies,
    'claim-race': scenario_claim_race,
    'workflow-orphan': scenario_workflow_orphan,
    'many-orphans': scenario_many_orphans,
    'claim-no-queue': scenario_claim_no_queue,
    'both-controllers-lost': scenario_both_controllers_lost,
    'exec-node-dies': scenario_exec_node_dies,
    'job-timeout': scenario_job_timeout,
    'fact-cache': scenario_fact_cache,
    'set-stats-artifacts': scenario_set_stats_artifacts,
    'job-slicing': scenario_job_slicing,
    'other-job-types': scenario_other_job_types,
    'waiting-jobs': scenario_waiting_jobs,
    'repeated-restarts': scenario_repeated_restarts,
    'large-replay': scenario_large_replay,
    'deprovision': scenario_deprovision,
    'data-check': scenario_data_check,
    'stats-insert-race': scenario_stats_insert_race,
    'dc-cleanup': scenario_dc_cleanup,
    'same-hosts': scenario_same_hosts,
    'few-workers': scenario_few_workers,
    'disable-live': scenario_disable_live,
    'capacity-race': scenario_capacity_race,
    'report': scenario_report,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('scenario', choices=['list', 'preflight', *SCENARIOS])
    parser.add_argument('--iterations', type=int, default=420, help='Loop items in the chatty playbook, about one second each')
    parser.add_argument('--claim-timeout', type=int, default=480)
    parser.add_argument('--finish-timeout', type=int, default=1200)
    parser.add_argument('--settle', type=int, default=45)
    parser.add_argument('--lead', type=int, default=20, help='Seconds of job output before the fault is injected')
    parser.add_argument('--observe', type=int, default=360, help='finalize-strand: seconds to watch the stranded job')
    parser.add_argument('--adopt-via', choices=['restart', 'peer', 'none'], default='restart', help='finalize-strand / host-map: who adopts')
    parser.add_argument('--quiet', type=int, default=360, help='quiet-deadline: seconds the silent task runs')
    parser.add_argument('--no-inject', action='store_true', help='quiet-deadline: do not fail the first unit status query')
    parser.add_argument('--outages', type=int, default=1, help='self-unavailable: consecutive failed health checks')
    parser.add_argument('--variant', help='per scenario; the first is the default: ' + '; '.join(f'{k}: {"|".join(v)}' for k, v in VARIANTS.items()))
    parser.add_argument('--down', type=int, default=150, help='both-controllers-lost: seconds both control nodes stay down')
    parser.add_argument('--job-timeout', type=int, default=90, help='job-timeout: the template timeout in seconds')
    parser.add_argument('--restarts', type=int, default=3, help='repeated-restarts: how many times the controller restarts')
    parser.add_argument('--restart-step', type=int, default=35, help='repeated-restarts: events between restarts')
    parser.add_argument('--events', type=int, default=20000, help='large-replay: burst events in bulk.yml')
    parser.add_argument('--hold-at', choices=['claim', 'stream'], default='stream', help='adopter-dies: where the first adopter is held and killed')
    parser.add_argument('--adopter-counter', type=int, default=60, help='adopter-dies --hold-at stream: the first adopter is held before this event')
    parser.add_argument('--cancel-in-adoption', action='store_true', help='claim-race: cancel the job once the winner is streaming')
    parser.add_argument('--orphans', type=int, default=30, help='many-orphans: jobs on the controller that dies')
    parser.add_argument('--sample', type=int, default=10, help='many-orphans: seconds between dispatcher pool samples')
    parser.add_argument('--count', type=int, default=3, help='capacity-disabled: jobs on the controller that dies')
    parser.add_argument(
        '--trigger', choices=['kill', 'stop', 'redis-blip', 'dispatcher'], default='kill', help='hybrid-resume / event-queue: how the node goes away'
    )
    parser.add_argument('--hybrid-setup', action='store_true', help='hybrid-resume: switch awx-1/awx-2 to hybrid first')
    parser.add_argument('--hybrid-teardown', action='store_true', help='hybrid-resume: switch them back to control afterwards')
    parser.add_argument('--backlog', type=int, default=20, help='event-queue: seconds of events to queue before the restart')
    parser.add_argument('--k8s-host', default='https://minikube:8443', help='log-rotation: Kubernetes API URL as the control nodes see it')
    parser.add_argument('--kubeconfig', help='log-rotation: kubeconfig for that cluster, from the host')
    parser.add_argument('--token-file', help='log-rotation: service account bearer token file')
    parser.add_argument('--minikube', default='minikube', help='log-rotation: minikube binary (to list pod log files)')
    parser.add_argument('--delay-adoption', type=int, default=0, help='log-rotation: seconds the adopter sleeps after its claim (adoption.after_claim)')
    parser.add_argument('--minikube-home', default='', help='log-rotation: MINIKUBE_HOME for that binary')
    parser.add_argument('--job', type=int, help='report: job id')
    parser.add_argument('--since', help='report: log start, UTC ISO with Z')
    parser.add_argument('--note', action='append', help='report: a note to print with the result')
    parser.add_argument('--mode', choices=['timing', 'seam'], default='timing', help='Drive the fault with sleeps and timers, or with failpoint seams')
    parser.add_argument('--seam-counter', type=int, default=25, help='seam: event counter before which the owner is held (the fault point)')
    parser.add_argument('--seam-backlog', type=int, default=20, help='event-queue seam: events queued in Redis at the kill')
    parser.add_argument(
        '--order', choices=['owner-first', 'adopter-first'], default='owner-first', help='slow-controller seam: which controller finalizes first'
    )
    parser.add_argument('--fresh-event-queries', action='store_true', help='slow-controller: delete EventQuery rows first so both finalizers insert them')
    parser.add_argument('--fail-host', default='', help='data-check / stats-insert-race: this host fails at the end of datacheck.yml')
    parser.add_argument('--constructed', action='store_true', help='data-check: run over a constructed inventory of the dc hosts')
    parser.add_argument('--abs-cpu', default='0.25', help='few-workers: SYSTEM_TASK_ABS_CPU for awx-2')
    parser.add_argument('--abs-mem', default='2348Mi', help='few-workers: SYSTEM_TASK_ABS_MEM for awx-2 (2 GiB is deducted, 100 MiB per fork)')
    parser.add_argument('--pending', type=int, default=3, help='capacity-race: pending launches queued before capacity is freed')
    parser.add_argument('--skip-preflight', action='store_true', help='Run even if the environment checks fail')
    parser.add_argument('--out', help='Directory to save logs, tracebacks and the timeline into')
    parser.add_argument('--max-lines', type=int, default=150)
    args = parser.parse_args()

    if args.scenario == 'list':
        for name, fn in SCENARIOS.items():
            print(f'{name}\n    {fn.__doc__.strip().splitlines()[0]}')
        return 0

    if args.scenario in VARIANTS:
        args.variant = args.variant or VARIANTS[args.scenario][0]
        if args.variant not in VARIANTS[args.scenario]:
            parser.error(f'{args.scenario} --variant must be one of {VARIANTS[args.scenario]}')

    containers = control_containers()
    if not containers:
        raise SystemExit('no tools_awx_N containers running')
    log(f'control containers: {", ".join(containers)}')
    args.branch = 'pr' if is_pr_branch(containers[0]) else 'devel'
    hosts = [c.replace('tools_', '').replace('_', '-') for c in containers] + ['receptor-1']
    if args.scenario != 'report':
        wait_cluster_ready(containers[0], hosts)
        problems = preflight(containers, hosts)
        for problem in problems:
            log(f'PREFLIGHT FAIL: {problem}')
        if args.scenario == 'preflight':
            log('preflight ok' if not problems else f'preflight: {len(problems)} problem(s)')
            return 1 if problems else 0
        if problems and not args.skip_preflight:
            log('environment not fit for a valid run; fix the above or pass --skip-preflight')
            return 2
    try:
        result = SCENARIOS[args.scenario](containers, args)
    finally:
        # Leave nothing armed for the next run (the hits stay for inspection).
        for c in containers:
            if manage(c, 'failpoint', 'disarm', '--all', check=False).returncode == 0:
                break
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
