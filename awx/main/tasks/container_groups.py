"""Kubernetes-side primitives for adopting container-group jobs.

A container-group job runs in a pod that receptor created, but the receptor work unit that
owns it lives in the *submitting controller's own* EE sidecar with an ephemeral datadir. When
that controller pod dies the work unit is gone permanently, so there is nothing to reattach
to and ``work_unit_id`` becomes a dangling reference. The mesh adoption path cannot help.

The job pod, though, is a separate Kubernetes object and survives. Kubernetes is itself the
durable cross-controller rendezvous: the Pod object is the record of liveness, the label
``ansible-awx-job-id`` is the link back to the job, and the log API serves the same
``ansible-runner worker`` event stream receptor would have relayed — during *and* after
execution. This module is the thin layer over those three facts.

The link is the label, not ``execution_node`` (always empty for container groups) and not the
pod name: AWX's ``automation-job-{id}`` is only a ``generateName`` prefix for receptor's
``CreatePod``, so the real name carries a random suffix.

Scope limit worth stating plainly: ``kubernetes-incluster-auth`` uses the controller pod's own
service account and the selector pins ``ansible-awx=<INSTALL_UUID>``, so this recovers from
controller-pod loss *within a surviving cluster*. In a true cluster-level failover the job pods
died with the cluster and there is nothing here to adopt.
"""

import io
import logging
import shutil

import ansible_runner

from django.conf import settings
from django.utils.timezone import now

from awx.main.dispatch.reaper import reap_job
from awx.main.models import UnifiedJob
from awx.main.scheduler.kubernetes import PodManager
from awx.main.tasks.adoption import invoke_adoption_hooks
from awx.main.tasks.receptor import (
    AWXReceptorJob,
    _AdoptionTask,
    _adoption_stall_budget_exhausted as budget_exhausted,
    _build_adoption_callback,
    _compute_adoption_dedup,
    _finalize_adopted_job,
    _get_or_create_private_data_dir,
    get_receptor_ctl,
    read_receptor_config,
    reattach_to_work_unit,
)

logger = logging.getLogger('awx.main.tasks.container_groups')

# Phases in which the pod is done and its log is complete.
TERMINAL_PHASES = ('Succeeded', 'Failed')
# Phases in which the pod may still be producing output.
LIVE_PHASES = ('Running', 'Pending')


class PodState:
    """Triage outcomes for a container-group job's pod.

    Adoption has to branch on what the pod is actually doing, because only one of these
    four cases is the familiar "attach and stream" shape.
    """

    #: No pod. Nothing survived the controller; the job is genuinely lost.
    ABSENT = 'absent'
    #: Pod finished. Its log is complete and static — harvest it and finalize from the exit
    #: code. No streaming lifecycle to manage, which makes this the cheapest case to recover.
    TERMINAL = 'terminal'
    #: Pod is live and has produced output, so the worker received its private data dir and
    #: is doing real work. Submit a work unit that attaches to it and stream it live.
    STREAMING = 'streaming'
    #: Pod is live but has been silent past the budget. ``ansible-runner worker`` blocks
    #: reading the private data dir from stdin, which receptor streams over the work unit; the
    #: controller died mid-transmit, so the worker is blocked forever and will never run the
    #: playbook. Not adoptable — delete the pod and let the job be requeued.
    WEDGED = 'wedged'
    #: Pod is live, silent, and still within the budget — or we cannot measure its age. A slow
    #: start looks exactly like a wedge, so defer and re-triage on the next heartbeat.
    WAITING = 'waiting'


def _pod_timestamp(pod):
    """When the pod's clock starts for wedge purposes.

    ``start_time`` is absent until the kubelet admits the pod, and a pod that never started
    is precisely the interesting case, so fall back to when the API server first saw it.
    """
    return pod.get('status', {}).get('start_time') or pod.get('metadata', {}).get('creation_timestamp')


def classify_job_pod(pod, has_output, wedge_timeout=None, reference_time=None):
    """Decide what can be recovered from a container-group job's pod.

    Args:
        pod: The pod as a dict (kubernetes client ``.to_dict()`` shape), or None if absent.
        has_output: Whether the pod has emitted at least one log line. Only consulted for
            live pods; see ``pod_has_output``, which must not be guessed at.
        wedge_timeout: Seconds of silence after which a live pod is considered wedged.
            Defaults to ``HADR_CONTAINER_GROUP_WEDGE_TIMEOUT``.
        reference_time: "Now", injectable for tests.

    Returns:
        One of the PodState constants.
    """
    if not pod:
        return PodState.ABSENT

    phase = pod.get('status', {}).get('phase')
    if phase in TERMINAL_PHASES:
        return PodState.TERMINAL

    # 'Unknown' means the kubelet is unreachable, which is a statement about the node's
    # connection to the API server and not about the pod. Condemning it here would delete a
    # pod that is very likely still running the playbook.
    if phase not in LIVE_PHASES:
        return PodState.WAITING

    if has_output:
        return PodState.STREAMING

    if wedge_timeout is None:
        wedge_timeout = settings.HADR_CONTAINER_GROUP_WEDGE_TIMEOUT

    started = _pod_timestamp(pod)
    if not started:
        # No measurable age means no deadline to be past, so keep waiting rather than
        # deleting a pod on a guess.
        return PodState.WAITING

    if reference_time is None:
        reference_time = now()

    if (reference_time - started).total_seconds() > wedge_timeout:
        return PodState.WEDGED
    return PodState.WAITING


def pod_exit_code(pod):
    """Exit code of a terminal pod's worker container.

    Prefers the container's own terminated state and only falls back to the pod phase, which
    collapses every nonzero code to 1. Note the explicit ``is not None``: a successful job
    exits 0, and a truthiness check would report it as failed.
    """
    for container_status in pod.get('status', {}).get('container_statuses') or []:
        terminated = (container_status.get('state') or {}).get('terminated') or {}
        code = terminated.get('exit_code')
        if code is not None:
            return int(code)

    return 0 if pod.get('status', {}).get('phase') == 'Succeeded' else 1


def find_job_pod(job):
    """The surviving pod for a container-group job, or None.

    Selects on both AWX labels: the job id alone would match a same-numbered job from another
    AWX installation sharing the namespace.
    """
    pm = PodManager(job)
    selector = f'ansible-awx={settings.INSTALL_UUID},ansible-awx-job-id={job.id}'
    response = pm.kube_api.list_namespaced_pod(
        pm.namespace,
        label_selector=selector,
        _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT,
    )
    items = response.to_dict().get('items') or []
    if not items:
        return None

    # A relaunch that reused the job id, or a pod receptor recreated, can leave two. The
    # newest is the one whose log we want; sort defensively since ordering is not guaranteed.
    def _sort_key(pod):
        ts = _pod_timestamp(pod)
        return (ts is not None, ts)

    return sorted(items, key=_sort_key)[-1]


def pod_has_output(job, pod_name):
    """Has the pod emitted at least one log line?

    This is the probe that separates a working pod from one wedged on stdin, and it runs on
    every heartbeat for every orphan, so it reads exactly one line. Errors propagate
    deliberately: a swallowed exception would read as "no output" and send a healthy pod to
    the reaper.

    ``_preload_content=False`` is not an optimisation here, it is the correctness fix. With the
    default preloading the client deserializes the body as ``str``, and because the declared
    response type is a plain string it ends up applying ``str()`` to the raw ``bytes`` — so an
    empty log comes back as the three-character string ``"b''"``, which is truthy. That made
    this function return True for every pod, silently turning WEDGED into STREAMING and
    disabling wedge detection entirely. Reading ``.data`` gives the real bytes.
    """
    pm = PodManager(job)
    resp = pm.kube_api.read_namespaced_pod_log(
        name=pod_name,
        namespace=pm.namespace,
        tail_lines=1,
        _preload_content=False,
        _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT,
    )
    try:
        return bool(resp.data and resp.data.strip())
    finally:
        resp.release_conn()


def open_pod_log_stream(job, pod_name, follow):
    """A file-like reader over the pod's log, ready for ansible-runner's Processor.

    The pod's stdout *is* the work unit's stdout: receptor's kube plugin captures the pod log
    and writes it to the unit's stdout file unchanged. So the same bytes the results socket
    would have carried can be fed to the same ``streamer='process'`` consumer.

    ``_preload_content=False`` is load-bearing twice over: it hands back the raw urllib3
    response, which supports the ``readline()`` the Processor needs, and it avoids buffering
    an entire multi-megabyte log into memory before the first event is handled. With
    ``follow=True`` it would never return at all.
    """
    pm = PodManager(job)
    return pm.kube_api.read_namespaced_pod_log(
        name=pod_name,
        namespace=pm.namespace,
        follow=follow,
        _preload_content=False,
    )


def delete_job_pod(job, pod_name):
    """Delete a job pod, returning whether it worked.

    Used to clear wedged pods, which ``awx_k8s_reaper`` will never touch: it only deletes pods
    whose job has left ACTIVE_STATES, and a wedged job is still 'running'. Failure is reported
    rather than raised so one unreachable pod does not abort the rest of the sweep.
    """
    try:
        pm = PodManager(job)
        pm.kube_api.delete_namespaced_pod(
            name=pod_name,
            namespace=pm.namespace,
            _request_timeout=settings.AWX_CONTAINER_GROUP_K8S_API_TIMEOUT,
        )
        return True
    except Exception:
        logger.exception(f'Failed to delete pod {pod_name} for {job.log_format}')
        return False


# ---------------------------------------------------------------------------
# Adoption
# ---------------------------------------------------------------------------


def requeue_wedged_job(job):
    """Hand a wedged job back to the task manager for a clean re-dispatch.

    Safe precisely because a wedged worker never got its private data dir and therefore never
    ran the playbook: there are no partial side effects for a re-run to collide with.

    Clearing work_unit_id matters as much as the status. It is the field the orphan scan keys
    on, so a requeued job that kept it would be picked up as orphaned again and sent back here
    to adopt a work unit that no longer exists. Mirrors how _reap_and_mark_lost_instance hands
    'waiting' jobs back. The status filter keeps this a no-op if another controller finalized
    the job between triage and now.
    """
    updated = UnifiedJob.objects.filter(pk=job.pk, status='running').update(
        status='pending',
        work_unit_id='',
        controller_node='',
        execution_node='',
    )
    if updated:
        logger.warning(f'{job.log_format}: pod never received its private data dir; requeued for re-dispatch')
    return bool(updated)


def harvest_terminal_pod(job, pod_name, pod):
    """Recover a finished container-group job from its pod's log.

    The pod's stdout is the work unit's stdout, so this feeds the same ansible-runner process
    streamer the live path uses, through the same counter-skip dedup — events already in the
    database are skipped, so replaying the log from the beginning is safe.

    Returns True if the job reached a terminal status, False if it should be retried later.
    """
    safe_threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    logger.info(
        f'{job.log_format}: harvesting terminal pod {pod_name}, safe_threshold={safe_threshold} '
        f'collision_zone_size={len(collision_zone)}, replaying the full pod log with counter-skip'
    )

    callback = _build_adoption_callback(job, safe_threshold, collision_zone)
    # Account for events already persisted so emitted_events and the EOF final_counter
    # describe the whole job rather than just this replay.
    callback.event_ct = persisted_ct

    private_data_dir = _get_or_create_private_data_dir(job)
    try:
        try:
            res = _process_pod_log(job, pod_name, callback, private_data_dir, follow=False)
        except Exception:
            # The log is static and the pod is not going anywhere, so a read failure is a
            # statement about the API connection. Retry rather than finalize on no output.
            logger.exception(f'{job.log_format}: failed reading the log of terminal pod {pod_name}, deferring')
            return False

        status, exit_code = _terminal_status(job, pod, res)

        hook_succeeded, hook_error = invoke_adoption_hooks(job, callback, private_data_dir, status)
        if not hook_succeeded:
            status = hook_error.get('status_override', 'failed')
            exit_code = 1
            if hook_error.get('explanation'):
                callback.delay_update(job_explanation=hook_error['explanation'])
            if hook_error.get('traceback'):
                callback.delay_update(result_traceback=hook_error['traceback'])

        _finalize_adopted_job(job, callback, exit_code, process_phase_failed=False, final_status=status)
        return True
    finally:
        shutil.rmtree(private_data_dir, ignore_errors=True)


def _process_pod_log(job, pod_name, callback, private_data_dir, follow):
    """Feed the pod's log to ansible-runner's process streamer.

    BufferedReader is not decoration: the Processor drives the stream with readline(), and
    urllib3's raw response would service that one byte at a time through io.IOBase.
    """
    stream = open_pod_log_stream(job, pod_name, follow=follow)
    try:
        return ansible_runner.interface.run(
            streamer='process',
            quiet=True,
            _input=io.BufferedReader(stream),
            event_handler=callback.event_handler,
            finished_callback=callback.finished_callback,
            status_handler=callback.status_handler,
            artifacts_handler=callback.artifacts_handler,
            private_data_dir=private_data_dir,
        )
    finally:
        try:
            stream.close()
        except Exception:
            pass


def _terminal_status(job, pod, res):
    """Final (status, exit_code) for a harvested pod.

    ansible-runner's own status line is preferred because it distinguishes a cancel from a
    failure, which an exit code cannot. It is not always available: kubelet rotates container
    logs at containerLogMaxSize, so a chatty job can lose the beginning of its own log and the
    Processor then reports 'error' for a job that actually succeeded. The pod's exit code
    survives rotation, so it is the fallback.
    """
    res_status = getattr(res, 'status', '') or ''
    if res_status in ('successful', 'failed', 'canceled'):
        return res_status, 0 if res_status == 'successful' else 1

    exit_code = pod_exit_code(pod)
    logger.warning(f'{job.log_format}: pod log yielded no usable final status ({res_status!r}); falling back to pod exit code {exit_code}')
    return ('successful' if exit_code == 0 else 'failed'), exit_code


def attach_to_streaming_pod(job, pod_name, pod, receptor_ctl=None):
    """Take over a container-group job whose pod is still running, by re-submitting it.

    The dead controller's work unit is unrecoverable, but the pod is not, and a new work unit
    carrying ``pod_name`` attaches to it instead of creating anything. Once that unit exists
    this is an ordinary adoption, so it hands straight off to ``reattach_to_work_unit`` and
    inherits the whole mesh path: counter-skip dedup, the stalled-stream watchdog, detach on
    shutdown, finalization and release.

    Rewriting ``work_unit_id`` is the point, not a side effect. It replaces a reference that
    can never resolve with one this controller owns, which is what makes ``work cancel`` reach
    the pod again and lets the next heartbeat use the plain receptor path.

    Returns True if the job reached a terminal status here, False if it should be re-triaged.
    """
    close_ctl = receptor_ctl is None
    if close_ctl:
        receptor_ctl = get_receptor_ctl(read_receptor_config())
    try:
        try:
            namespace = pod['metadata']['namespace']
            receptor_job = AWXReceptorJob(_AdoptionTask(job, None), {'private_data_dir': None})
            unit_id = receptor_job.submit_pod_attach(receptor_ctl, pod_name, namespace)
            unit_status = receptor_ctl.simple_command(f'work status {unit_id}')
        except Exception:
            # A failed submit creates no pod and changes nothing about the job, so this is a
            # statement about this controller's receptor. Defer and re-triage.
            logger.exception(f'{job.log_format}: could not attach a work unit to running pod {pod_name}, deferring adoption')
            return False

        logger.info(f'{job.log_format}: attached work unit {unit_id} to running pod {pod_name} in {namespace}, streaming live')
        UnifiedJob.objects.filter(pk=job.pk).update(work_unit_id=unit_id)
        job.work_unit_id = unit_id

        return bool(reattach_to_work_unit(job, receptor_ctl, unit_status=unit_status))
    finally:
        if close_ctl:
            try:
                receptor_ctl.close()
            except Exception:
                pass


def adopt_container_group_job(job, receptor_ctl=None):
    """Recover a container-group job whose controller died, using its surviving pod.

    Called only once the receptor path has established that the work unit is unreachable,
    which for a container group means the submitting controller took it to the grave.

    Returns True if the job reached a terminal state (or was requeued) and needs no further
    attention, False if it should be re-triaged on the next heartbeat.
    """
    try:
        pod = find_job_pod(job)
        # A finished pod is harvested whatever the probe would say, so skip the API call.
        phase = (pod or {}).get('status', {}).get('phase')
        has_output = False if (pod is None or phase in TERMINAL_PHASES) else pod_has_output(job, pod['metadata']['name'])
        state = classify_job_pod(pod, has_output=has_output)
    except Exception:
        # An unreachable Kubernetes API is a statement about this controller's connection,
        # not about the pod. Guessing here would delete live pods or fail live jobs.
        logger.exception(f'{job.log_format}: could not triage container-group pod, deferring adoption')
        return False

    pod_name = pod['metadata']['name'] if pod else None
    logger.info(f'{job.log_format}: container-group pod triage = {state} (pod={pod_name})')

    if state == PodState.TERMINAL:
        return harvest_terminal_pod(job, pod_name, pod)

    if state == PodState.WEDGED:
        if not delete_job_pod(job, pod_name):
            # Requeuing now would let the task manager launch a second pod carrying the same
            # ansible-awx-job-id label, and find_job_pod could then pick either one.
            logger.warning(f'{job.log_format}: wedged pod {pod_name} could not be deleted, deferring requeue')
            return False
        requeue_wedged_job(job)
        return True

    if state == PodState.ABSENT:
        if not budget_exhausted(job):
            # The pod may simply not have been created yet when the controller died.
            logger.info(f'{job.log_format}: no container-group pod found yet, deferring adoption')
            return False
        logger.error(f'{job.log_format}: container-group pod is gone and the adoption deadline has passed, failing')
        reap_job(job, 'failed', job_explanation='Job pod did not survive the loss of its controller and could not be recovered.')
        return True

    if state == PodState.STREAMING:
        return attach_to_streaming_pod(job, pod_name, pod, receptor_ctl=receptor_ctl)

    # WAITING defers. The pod is silent and still inside the wedge budget, so a slow start and
    # a wedge are indistinguishable; the next triage tells them apart. It is deliberately not
    # subject to the adoption deadline — adoption emits no events while it waits, so the
    # orphan measure would condemn a job that is merely starting slowly.
    return False
