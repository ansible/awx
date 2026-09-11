def create_job(jt, dependencies_processed=True, scm_branch=None):
    job = jt.create_unified_job()
    job.status = "pending"
    job.dependencies_processed = dependencies_processed
    if scm_branch is not None:
        job.scm_branch = scm_branch
    job.save()
    return job
