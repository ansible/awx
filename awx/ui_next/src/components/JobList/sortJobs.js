const sortFns = {
  finished: byFinished,
  id: byId,
  name: byName,
  created_by__id: byCreatedBy,
  unified_job_template__project__id: byProject,
  started: byStarted,
};

export default function sortJobs(jobs, params) {
  const { order_by = '-finished', page_size = 20 } = params;
  const key = order_by.replace('-', '');
  const fn = sortFns[key];
  if (!fn) {
    return jobs.slice(0, page_size);
  }

  const sorted = order_by[0] === '-' ? jobs.sort(reverse(fn)) : jobs.sort(fn);
  return sorted.slice(0, page_size);
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
    return 1;
  }
  if (!b.started) {
    return -1;
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
  const nameA = a.summary_fields?.created_by?.id;
  const nameB = b.summary_fields?.created_by?.id;
  return sort(nameA, nameB) * -1;
}

function byProject(a, b) {
  return sort(a.unified_job_template, b.unified_job_template);
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
