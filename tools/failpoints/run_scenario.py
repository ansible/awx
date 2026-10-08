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
          events=j.get_event_queryset().count(),
          last_event_age=(now() - last).total_seconds() if last else None))
''',
    )


def instances(container):
    return orm(
        container,
        '''
from awx.main.models import Instance
emit({i.hostname: dict(state=i.node_state, capacity=i.capacity, errors=i.errors, last_seen=i.last_seen)
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


def setup(containers, jt_name, playbook, extra_vars):
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
inv = Inventory.objects.get(name='Demo Inventory')
proj, _ = Project.objects.get_or_create(name='failpoint scenarios',
    defaults=dict(organization=org, scm_type='', local_path={PROJECT_NAME!r}))
jt, _ = JobTemplate.objects.get_or_create(name={jt_name!r},
    defaults=dict(project=proj, inventory=inv, playbook={playbook!r}, organization=org))
jt.extra_vars = json.dumps({extra_vars!r})
jt.save()
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


def start_job(containers, args, jt_name='failpoint chatty', playbook='chatty.yml', extra_vars=None):
    """Reset failpoints, launch a job and wait until it runs remotely with a work unit."""
    c0 = containers[0]
    manage(c0, 'failpoint', 'disarm', '--all')
    manage(c0, 'failpoint', 'clear-hits')
    jt_id = setup(containers, jt_name, playbook, extra_vars or {'iterations': args.iterations})
    job_id = launch(c0, jt_id)
    log(f'launched job {job_id} from template {jt_id} ({playbook} {extra_vars or {"iterations": args.iterations}})')
    st = wait_for('job running with a work unit', lambda: (s := job_state(c0, job_id))['status'] == 'running' and s['work_unit_id'] and s, 300)
    log(f"job {job_id} running: controller={st['controller_node']} execution={st['execution_node']} unit={st['work_unit_id']}")
    if st['execution_node'] == st['controller_node']:
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


SCENARIOS = {
    'slow-controller': scenario_slow_controller,
    'finalize-strand': scenario_finalize_strand,
    'quiet-deadline': scenario_quiet_deadline,
    'self-unavailable': scenario_self_unavailable,
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
    parser.add_argument('--adopt-via', choices=['restart', 'peer'], default='restart', help='finalize-strand: who adopts')
    parser.add_argument('--quiet', type=int, default=360, help='quiet-deadline: seconds the silent task runs')
    parser.add_argument('--no-inject', action='store_true', help='quiet-deadline: do not fail the first unit status query')
    parser.add_argument('--outages', type=int, default=1, help='self-unavailable: consecutive failed health checks')
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
    wait_cluster_ready(containers[0], hosts)
    result = SCENARIOS[args.scenario](containers, args)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
