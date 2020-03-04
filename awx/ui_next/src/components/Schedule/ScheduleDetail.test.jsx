import React from 'react';
import { SchedulesAPI } from '@api';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import ScheduleDetail from './ScheduleDetail';

jest.mock('@api/models/Schedules');

const schedule = {
  url: '/api/v2/schedules/1',
  rrule:
    'DTSTART;TZID=America/New_York:20200220T000000 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1',
  id: 1,
  summary_fields: {
    unified_job_template: {
      id: 1,
      name: 'Mock JT',
      description: '',
      unified_job_type: 'job',
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    inventory: {
      id: 1,
      name: 'Test Inventory',
    },
  },
  created: '2020-03-03T20:38:54.210306Z',
  modified: '2020-03-03T20:38:54.210336Z',
  name: 'Mock JT Schedule',
  enabled: false,
  description: 'A good schedule',
  timezone: 'America/New_York',
  dtstart: '2020-03-16T04:00:00Z',
  dtend: '2020-07-06T04:00:00Z',
  next_run: '2020-03-16T04:00:00Z',
};

SchedulesAPI.createPreview.mockResolvedValue({
  data: {
    local: [],
    utc: [],
  },
});

describe('<ScheduleDetail />', () => {
  let wrapper;
  const history = createMemoryHistory({
    initialEntries: ['/templates/job_template/1/schedules/1/details'],
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('details should render with the proper values without prompts', async () => {
    SchedulesAPI.readCredentials.mockResolvedValueOnce({
      data: {
        count: 0,
        results: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/job_template/:id/schedules/:scheduleId"
          component={() => <ScheduleDetail schedule={schedule} />}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(
      wrapper
        .find('Detail[label="Name"]')
        .find('dd')
        .text()
    ).toBe('Mock JT Schedule');
    expect(
      wrapper
        .find('Detail[label="Description"]')
        .find('dd')
        .text()
    ).toBe('A good schedule');
    expect(wrapper.find('Detail[label="First Run"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Next Run"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Last Run"]').length).toBe(1);
    expect(
      wrapper
        .find('Detail[label="Local Time Zone"]')
        .find('dd')
        .text()
    ).toBe('America/New_York');
    expect(wrapper.find('Detail[label="Repeat Frequency"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Created"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Last Modified"]').length).toBe(1);
    expect(wrapper.find('Title[children="Prompted Fields"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Job Type"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Inventory"]').length).toBe(0);
    expect(wrapper.find('Detail[label="SCM Branch"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Limit"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Show Changes"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Credentials"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Job Tags"]').length).toBe(0);
    expect(wrapper.find('Detail[label="Skip Tags"]').length).toBe(0);
  });
  test('details should render with the proper values with prompts', async () => {
    SchedulesAPI.readCredentials.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          {
            id: 1,
            name: 'Cred 1',
          },
          {
            id: 2,
            name: 'Cred 2',
          },
        ],
      },
    });
    const scheduleWithPrompts = {
      ...schedule,
      job_type: 'run',
      inventory: 1,
      job_tags: 'tag1',
      skip_tags: 'tag2',
      scm_branch: 'foo/branch',
      limit: 'localhost',
      diff_mode: true,
      verbosity: 1,
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/job_template/:id/schedules/:scheduleId"
          component={() => <ScheduleDetail schedule={scheduleWithPrompts} />}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(
      wrapper
        .find('Detail[label="Name"]')
        .find('dd')
        .text()
    ).toBe('Mock JT Schedule');
    expect(
      wrapper
        .find('Detail[label="Description"]')
        .find('dd')
        .text()
    ).toBe('A good schedule');
    expect(wrapper.find('Detail[label="First Run"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Next Run"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Last Run"]').length).toBe(1);
    expect(
      wrapper
        .find('Detail[label="Local Time Zone"]')
        .find('dd')
        .text()
    ).toBe('America/New_York');
    expect(wrapper.find('Detail[label="Repeat Frequency"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Created"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Last Modified"]').length).toBe(1);
    expect(wrapper.find('Title[children="Prompted Fields"]').length).toBe(1);
    expect(
      wrapper
        .find('Detail[label="Job Type"]')
        .find('dd')
        .text()
    ).toBe('run');
    expect(wrapper.find('Detail[label="Inventory"]').length).toBe(1);
    expect(
      wrapper
        .find('Detail[label="SCM Branch"]')
        .find('dd')
        .text()
    ).toBe('foo/branch');
    expect(
      wrapper
        .find('Detail[label="Limit"]')
        .find('dd')
        .text()
    ).toBe('localhost');
    expect(wrapper.find('Detail[label="Show Changes"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Credentials"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Job Tags"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Skip Tags"]').length).toBe(1);
  });
  test('error shown when error encountered fetching credentials', async () => {
    SchedulesAPI.readCredentials.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/job_templates/1/schedules/1/credentials',
          },
          data: 'An error occurred',
          status: 500,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/job_template/:id/schedules/:scheduleId"
          component={() => <ScheduleDetail schedule={schedule} />}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
