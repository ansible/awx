export default function getScheduleUrl(job) {
  const templateId = job.summary_fields.unified_job_template.id;
  const scheduleId = job.summary_fields.schedule.id;
  const inventoryId = job.summary_fields.inventory
    ? job.summary_fields.inventory.id
    : null;
  let scheduleUrl;

  switch (job.type) {
    case 'inventory_update':
      scheduleUrl =
        inventoryId &&
        `/inventories/inventory/${inventoryId}/sources/${templateId}/schedules/${scheduleId}/details`;
      break;
    case 'job':
      scheduleUrl = `/templates/job_template/${templateId}/schedules/${scheduleId}/details`;
      break;
    case 'project_update':
      scheduleUrl = `/projects/${templateId}/schedules/${scheduleId}/details`;
      break;
    case 'system_job':
      scheduleUrl = `/management_jobs/${templateId}/schedules/${scheduleId}/details`;
      break;
    case 'workflow_job':
      scheduleUrl = `/templates/workflow_job_template/${templateId}/schedules/${scheduleId}/details`;
      break;
    default:
      break;
  }

  return scheduleUrl;
}
