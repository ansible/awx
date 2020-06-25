const sortFns = {
  finished: byFinished,
  id: byId,
  name: byName,
  created_by__id: byCreatedBy,
  unified_job_template__project__id: byProject,
  started: byStarted,
};

export default function sortJobs(jobs, orderBy) {
  const key = orderBy.replace('-', '');
  const fn = sortFns[key];
  if (!fn) {
    return jobs;
  }

  return orderBy[0] === '-' ? jobs.sort(reverse(fn)) : jobs.sort(fn);
}

function reverse(fn) {
  return (a, b) => fn(a, b) * -1;
}

function byFinished(a, b) {
  if (!a.finished) {
    return 1;
  }
  if (!b.finished) {
    return -1;
  }
  return sort(new Date(a.finished), new Date(b.finished));
}

function byStarted(a, b) {
  if (!a.started) {
    return -1;
  }
  if (!b.started) {
    return 1;
  }
  return sort(new Date(a.started), new Date(b.started));
}

function byId(a, b) {
  return sort(a.id, b.id);
}

function byName(a, b) {
  return sort(a.name, b.name);
}

function byCreatedBy(a, b) {
  const nameA = a.summary_fields?.created_by?.username;
  const nameB = b.summary_fields?.created_by?.username;
  return sort(nameA, nameB);
}

function byProject(a, b) {
  const projA = a.summary_fields?.project?.id;
  const projB = b.summary_fields?.project?.id;
  return sort(projA, projB);
}

function sort(a, b) {
  if (!a) {
    return -1;
  }
  if (!b) {
    return 1;
  }
  if (a < b) {
    return -1;
  }
  if (a > b) {
    return 1;
  }
  return 0;
}
