def create_job(jt, dependencies_processed=True):
    job = jt.create_unified_job()
    job.status = "pending"
    job.dependencies_processed = dependencies_processed
    job.save()
    return job
