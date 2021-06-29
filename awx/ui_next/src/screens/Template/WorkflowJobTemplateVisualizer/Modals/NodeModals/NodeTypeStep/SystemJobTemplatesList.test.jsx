import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';
import { SystemJobTemplatesAPI } from '../../../../../../api';
import SystemJobTemplatesList from './SystemJobTemplatesList';

jest.mock('../../../../../../api/models/SystemJobTemplates');

const nodeResource = {
  id: 1,
  type: 'system_job_template',
  url: '/api/v2/system_job_templates/1/',
  related: {
    next_schedule: '/api/v2/schedules/1/',
    jobs: '/api/v2/system_job_templates/1/jobs/',
    schedules: '/api/v2/system_job_templates/1/schedules/',
    launch: '/api/v2/system_job_templates/1/launch/',
    notification_templates_started:
      '/api/v2/system_job_templates/1/notification_templates_started/',
    notification_templates_success:
      '/api/v2/system_job_templates/1/notification_templates_success/',
    notification_templates_error:
      '/api/v2/system_job_templates/1/notification_templates_error/',
  },
  summary_fields: {},
  created: '2021-06-29T18:58:47.571901Z',
  modified: '2021-06-29T18:58:47.571901Z',
  name: 'Cleanup Job Details',
  description: 'Remove job history',
  last_job_run: null,
  last_job_failed: false,
  next_job_run: '2021-07-04T18:58:47Z',
  status: 'ok',
  execution_environment: null,
  job_type: 'cleanup_jobs',
};
const onUpdateNodeResource = jest.fn();

describe('SystemJobTemplatesList', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('Row selected when nodeResource id matches row id and clicking new row makes expected callback', async () => {
    SystemJobTemplatesAPI.read.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          nodeResource,
          {
            id: 2,
            type: 'system_job_template',
            url: '/api/v2/system_job_templates/2/',
            related: {
              last_job: '/api/v2/system_jobs/3/',
              next_schedule: '/api/v2/schedules/2/',
              jobs: '/api/v2/system_job_templates/2/jobs/',
              schedules: '/api/v2/system_job_templates/2/schedules/',
              launch: '/api/v2/system_job_templates/2/launch/',
              notification_templates_started:
                '/api/v2/system_job_templates/2/notification_templates_started/',
              notification_templates_success:
                '/api/v2/system_job_templates/2/notification_templates_success/',
              notification_templates_error:
                '/api/v2/system_job_templates/2/notification_templates_error/',
            },
            summary_fields: {
              last_job: {
                id: 3,
                name: 'Cleanup Activity Stream',
                description: 'Remove activity stream history',
                finished: '2021-06-29T20:38:22.770364Z',
                status: 'successful',
                failed: false,
              },
              last_update: {
                id: 3,
                name: 'Cleanup Activity Stream',
                description: 'Remove activity stream history',
                status: 'successful',
                failed: false,
              },
            },
            created: '2021-06-29T18:58:47.571901Z',
            modified: '2021-06-29T18:58:47.571901Z',
            name: 'Cleanup Activity Stream',
            description: 'Remove activity stream history',
            last_job_run: '2021-06-29T20:38:22.770364Z',
            last_job_failed: false,
            next_job_run: '2021-07-06T18:58:47Z',
            status: 'successful',
            execution_environment: null,
            job_type: 'cleanup_activitystream',
          },
        ],
      },
    });
    SystemJobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SystemJobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="Cleanup Job Details"]').props()
        .isSelected
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="Cleanup Activity Stream"]').props()
        .isSelected
    ).toBe(false);
    wrapper
      .find('CheckboxListItem[name="Cleanup Activity Stream"]')
      .prop('onSelect')();
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 2,
      type: 'system_job_template',
      url: '/api/v2/system_job_templates/2/',
      related: {
        last_job: '/api/v2/system_jobs/3/',
        next_schedule: '/api/v2/schedules/2/',
        jobs: '/api/v2/system_job_templates/2/jobs/',
        schedules: '/api/v2/system_job_templates/2/schedules/',
        launch: '/api/v2/system_job_templates/2/launch/',
        notification_templates_started:
          '/api/v2/system_job_templates/2/notification_templates_started/',
        notification_templates_success:
          '/api/v2/system_job_templates/2/notification_templates_success/',
        notification_templates_error:
          '/api/v2/system_job_templates/2/notification_templates_error/',
      },
      summary_fields: {
        last_job: {
          id: 3,
          name: 'Cleanup Activity Stream',
          description: 'Remove activity stream history',
          finished: '2021-06-29T20:38:22.770364Z',
          status: 'successful',
          failed: false,
        },
        last_update: {
          id: 3,
          name: 'Cleanup Activity Stream',
          description: 'Remove activity stream history',
          status: 'successful',
          failed: false,
        },
      },
      created: '2021-06-29T18:58:47.571901Z',
      modified: '2021-06-29T18:58:47.571901Z',
      name: 'Cleanup Activity Stream',
      description: 'Remove activity stream history',
      last_job_run: '2021-06-29T20:38:22.770364Z',
      last_job_failed: false,
      next_job_run: '2021-07-06T18:58:47Z',
      status: 'successful',
      execution_environment: null,
      job_type: 'cleanup_activitystream',
    });
  });
  test('Error shown when read() request errors', async () => {
    SystemJobTemplatesAPI.read.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SystemJobTemplatesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
