import getScheduleUrl from './getScheduleUrl';

describe('getScheduleUrl', () => {
  test('should return expected schedule URL for inventory update job', () => {
    const invSrcJob = {
      type: 'inventory_update',
      summary_fields: {
        inventory: {
          id: 1,
          name: 'mock inv',
        },
        schedule: {
          name: 'mock schedule',
          id: 3,
        },
        unified_job_template: {
          unified_job_type: 'inventory_update',
          name: 'mock inv src',
          id: 2,
        },
      },
    };
    expect(getScheduleUrl(invSrcJob)).toEqual(
      '/inventories/inventory/1/sources/2/schedules/3/details'
    );
  });
  test('should return expected schedule URL for job', () => {
    const templateJob = {
      type: 'job',
      summary_fields: {
        schedule: {
          name: 'mock schedule',
          id: 5,
        },
        unified_job_template: {
          unified_job_type: 'job',
          name: 'mock job',
          id: 4,
        },
      },
    };
    expect(getScheduleUrl(templateJob)).toEqual(
      '/templates/job_template/4/schedules/5/details'
    );
  });
  test('should return expected schedule URL for project update job', () => {
    const projectUpdateJob = {
      type: 'project_update',
      summary_fields: {
        schedule: {
          name: 'mock schedule',
          id: 7,
        },
        unified_job_template: {
          unified_job_type: 'project_update',
          name: 'mock job',
          id: 6,
        },
      },
    };
    expect(getScheduleUrl(projectUpdateJob)).toEqual(
      '/projects/6/schedules/7/details'
    );
  });
  test('should return expected schedule URL for system job', () => {
    const systemJob = {
      type: 'system_job',
      summary_fields: {
        schedule: {
          name: 'mock schedule',
          id: 10,
        },
        unified_job_template: {
          unified_job_type: 'system_job',
          name: 'mock job',
          id: 9,
        },
      },
    };
    expect(getScheduleUrl(systemJob)).toEqual(
      '/management_jobs/9/schedules/10/details'
    );
  });
  test('should return expected schedule URL for workflow job', () => {
    const workflowJob = {
      type: 'workflow_job',
      summary_fields: {
        schedule: {
          name: 'mock schedule',
          id: 12,
        },
        unified_job_template: {
          unified_job_type: 'job',
          name: 'mock job',
          id: 11,
        },
      },
    };
    expect(getScheduleUrl(workflowJob)).toEqual(
      '/templates/workflow_job_template/11/schedules/12/details'
    );
  });
});
