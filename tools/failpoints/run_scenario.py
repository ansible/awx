#!/usr/bin/env python3
"""Run a failure scenario against the docker-compose dev cluster, then check invariants.

Runs on the host. It drives the cluster only through `docker exec ... awx-manage`, so it
needs no AWX install of its own. Start the cluster with at least two control nodes and one
execution node first, for example:

    MAIN_NODE_TYPE=control make docker-compose COMPOSE_TAG=devel \
        CONTROL_PLANE_NODE_COUNT=2 EXECUTION_NODE_COUNT=1

Then:

    tools/failpoints/run_scenario.py list
    tools/failpoints/run_scenario.py slow-controller --out /tmp/fp-runs

Each scenario prints a timeline, the failpoint hits, the adoption-related log lines and the
invariant results for the job, and exits non-zero if any invariant failed. With --out it
also saves the full timestamped container logs, every traceback, and a merged per-node
event timeline (UTC, ms) for the run.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(HERE, 'project')
PROJECT_NAME = 'failpoint_scenarios'
PLAYBOOKS = ('chatty.yml', 'quiet.yml')
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
    return run(['docker', 'exec', '-i', container, 'awx-manage', *args], check=check)


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


def setup(containers, jt_name, playbook, extra_vars, inventory='Demo Inventory', allow_simultaneous=False, instance_group=None):
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
stats = list(qs.filter(event='playbook_on_stats').values_list('created', 'counter'))
for created, counter in stats:
    rows.append(('db', f'playbook_on_stats row (counter {{counter}})', created))
for n in j.notifications.all().order_by('created'):
    rows.append(('db', f'notification {{n.id}} subject={{n.subject!r}} status={{n.status}}', n.created))
for h in failpoints.hits(fired_only=True):
    rows.append((h['node'], f"failpoint {{h['name']}} fired action={{h['action']}} ctx={{h['ctx']}}", h['at']))
emit([(str(at), node, what) for node, what, at in rows if at])
''',
    )


def report(containers, job_id, since, args, unit_id=None, notes=()):
    alive = [c for c in containers if manage(c, 'failpoint', 'list', check=False).returncode == 0]
    c = alive[0]
    hits = json.loads(manage(c, 'failpoint', 'hits', '--fired').stdout)
    result = json.loads(manage(c, 'failpoint', 'check-job', str(job_id)).stdout)
    out_dir = None
    if args.out:
        out_dir = os.path.join(args.out, f'{args.scenario}-job{job_id}')
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
    if out_dir:
        with open(os.path.join(out_dir, 'result.json'), 'w') as fh:
            json.dump({'job_id': job_id, 'hits': hits, 'result': result, 'events': events, 'tracebacks': tbs}, fh, indent=2, default=str)
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
    """
    if len(containers) < 2:
        raise SystemExit('slow-controller needs at least two control nodes')
    c0 = containers[0]
    since = since_now()
    job_id, st = start_job(containers, args)
    owner = st['controller_node']

    manage(c0, 'failpoint', 'arm', 'heartbeat.start', '--action', 'pause', '--match', f'node={owner}', '--match', 'periodic=True', '--timeout', '1200')
    log(f'armed heartbeat.start pause on {owner}')
    manage(c0, 'failpoint', 'wait', 'heartbeat.start', '--timeout', '120')
    log(f'{owner} heartbeat is paused; waiting for a peer to claim job {job_id}')

    notes = []
    try:
        st = wait_for('a peer to claim the job', lambda: (s := job_state(c0, job_id))['controller_node'] != owner and s, args.claim_timeout)
        log(f"job {job_id} claimed by {st['controller_node']} (status={st['status']})")
    except TimeoutError as exc:
        notes.append(f'no peer claimed the job: {exc}')
        log(notes[-1])
    finally:
        peer = next(c for c in containers if c != container_for(owner))
        manage(peer, 'failpoint', 'release', 'heartbeat.start', check=False)
        manage(peer, 'failpoint', 'disarm', 'heartbeat.start', check=False)
        log(f'released {owner} heartbeat; both controllers are live again')

    wait_finished(c0, job_id, args.finish_timeout)
    log(f'waiting {args.settle}s for callback receivers and notifications to settle')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, st['work_unit_id'], notes)


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
    """
    c0 = containers[0]
    pr = is_pr_branch(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    notes = [f'branch={"PR" if pr else "devel"} variant={args.variant}']
    time.sleep(args.lead)

    if args.variant == 'task-id-window':
        if not pr:
            raise SystemExit('task-id-window needs the PR branch (_queue_job_adoption)')
        manage(peer, 'failpoint', 'arm', 'adoption.before_task_id_saved', '--action', 'pause', '--match', f'job_id={job_id}', '--timeout', '600')
        log('armed adoption.before_task_id_saved pause')
    if args.variant == 'deferred':
        manage(peer, 'failpoint', 'arm', 'adoption.unit_status', '--action', 'raise', '--match', f'job_id={job_id}', '--times', '2')
        log('armed adoption.unit_status raise (times=2): the first adoption attempt defers')

    run(['docker', 'kill', oc])
    log(f'docker kill {oc}')

    def do_cancel(why):
        res = cancel_job(peer, job_id)
        log(f'cancel ({why}): {res}')
        notes.append(
            f"cancel issued at {res['at']} ({why}); addressed to controller_node={res['sent_to']['controller_node']} task={res['sent_to']['celery_task_id']}; log: {res['log']!r}"
        )

    if args.variant in ('dead', 'restart'):
        time.sleep(5)
        do_cancel(f'{owner} is dead')
    if args.variant == 'restart':
        start_back(oc, owner)
    if args.variant == 'deferred':
        start_back(oc, owner)
        hits = wait_for(
            'two adoption.unit_status raises',
            lambda: len(json.loads(manage(peer, 'failpoint', 'hits', 'adoption.unit_status', '--fired').stdout)) >= 2 or None,
            300,
            poll=1,
        )
        log(f'adoption.unit_status fired twice; the adoption deferred ({hits})')
        time.sleep(2)
        do_cancel('adoption deferred, before the next heartbeat re-queues it')
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
    notes.append(f"exec-node unit after the job ended: {unit_status(unit)}; playbook processes: {exec_node_processes(r'ansible-playbook')}")
    log(notes[-1])
    if args.variant in ('dead', 'task-id-window'):
        start_back(oc, owner)
    manage(peer, 'failpoint', 'disarm', '--all')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes)


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
    """
    c0 = containers[0]
    pr = is_pr_branch(c0)
    since = since_now()
    job_id, st = start_job(containers, args)
    owner, unit = st['controller_node'], st['work_unit_id']
    oc = container_for(owner)
    peer = next(c for c in containers if c != oc)
    notes = [f"branch={'PR' if pr else 'devel'} trigger={args.trigger}"]
    # Armed only to record the snapshot: an unarmed failpoint leaves no hit to wait on.
    manage(peer, 'failpoint', 'arm', 'adoption.after_snapshot', '--action', 'sleep', '--seconds', '0', '--match', f'job_id={job_id}')
    time.sleep(args.lead)
    manage(peer, 'failpoint', 'arm', 'callback_receiver.before_flush', '--action', 'pause', '--match', f'node={owner}', '--timeout', '1200')
    log(f'armed callback_receiver.before_flush pause on {owner}')
    manage(peer, 'failpoint', 'wait', 'callback_receiver.before_flush', '--timeout', '60')
    time.sleep(args.backlog)
    s = job_state(peer, job_id)
    notes.append(f"before restart: {s['events']} events in DB, Redis backlog on {owner}: {redis_backlog(oc)}")
    log(notes[-1])
    if args.trigger == 'kill':
        kill_and_restart(oc, peer, owner)
    else:
        if pr:
            manage(peer, 'failpoint', 'arm', 'sweep.before_claim', '--action', 'raise', '--match', f'node={container_for_host(peer)}')
            log('armed sweep.before_claim raise on the peer: it must not steal the job')
        run(['docker', 'exec', oc, 'supervisorctl', 'restart', 'tower-processes:awx-dispatcher'])
        log(f'restarted the dispatcher on {owner}')
    hit = json.loads(manage(peer, 'failpoint', 'wait', 'adoption.after_snapshot', '--timeout', str(args.finish_timeout)).stdout)
    log(f"adoption snapshot on {hit['node']} at {hit['at']}: {hit['ctx']}")
    notes.append(f"adoption snapshot at {hit['at']} on {hit['node']}: {hit['ctx']}")
    time.sleep(10)
    notes.append(f"at release: {job_state(peer, job_id)['events']} events in DB, Redis backlog: {redis_backlog(oc)}")
    log(notes[-1])
    manage(peer, 'failpoint', 'release', 'callback_receiver.before_flush')
    time.sleep(2)
    manage(peer, 'failpoint', 'disarm', 'callback_receiver.before_flush')
    log('released and disarmed callback_receiver.before_flush')
    wait_finished(peer, job_id, args.finish_timeout)
    manage(peer, 'failpoint', 'disarm', '--all')
    time.sleep(args.settle)
    return report(containers, job_id, since, args, unit, notes)


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
        with open(os.path.join(args.out, f'{args.scenario}-job{job_id}', 'hostmap.json'), 'w') as fh:
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


def scenario_report(containers, args):
    """Report only: invariants, timeline and saved logs for --job since --since (a run cut short)."""
    if not (args.job and args.since):
        raise SystemExit('report needs --job and --since')
    alive = [c for c in containers if manage(c, 'failpoint', 'list', check=False).returncode == 0]
    unit = job_state(alive[0], args.job)['work_unit_id']
    return report(containers, args.job, args.since, args, unit, args.note or ())


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
    'report': scenario_report,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('scenario', choices=['list', *SCENARIOS])
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
    parser.add_argument('--variant', choices=['dead', 'restart', 'task-id-window', 'deferred'], default='dead', help='cancel-orphan: when the cancel is issued')
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
    parser.add_argument('--out', help='Directory to save logs, tracebacks and the timeline into')
    parser.add_argument('--max-lines', type=int, default=150)
    args = parser.parse_args()

    if args.scenario == 'list':
        for name, fn in SCENARIOS.items():
            print(f'{name}\n    {fn.__doc__.strip().splitlines()[0]}')
        return 0

    containers = control_containers()
    if not containers:
        raise SystemExit('no tools_awx_N containers running')
    log(f'control containers: {", ".join(containers)}')
    hosts = [c.replace('tools_', '').replace('_', '-') for c in containers] + ['receptor-1']
    if args.scenario != 'report':
        wait_cluster_ready(containers[0], hosts)
    result = SCENARIOS[args.scenario](containers, args)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
