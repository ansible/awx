import React from 'react';
import { SchedulesAPI } from '@api';
import { Route } from 'react-router-dom';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import Schedule from './Schedule';

jest.mock('@api/models/Schedules');

SchedulesAPI.readDetail.mockResolvedValue({
  data: {
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
    },
    created: '2020-03-03T20:38:54.210306Z',
    modified: '2020-03-03T20:38:54.210336Z',
    name: 'Mock JT Schedule',
    next_run: '2020-02-20T05:00:00Z',
  },
});

SchedulesAPI.createPreview.mockResolvedValue({
  data: {
    local: [],
    utc: [],
  },
});

SchedulesAPI.readCredentials.mockResolvedValue({
  data: {
    count: 0,
    results: [],
  },
});

describe('<Schedule />', () => {
  let wrapper;
  let history;
  const unifiedJobTemplate = { id: 1, name: 'Mock JT' };
  beforeAll(async () => {
    history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/schedules/1/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/job_template/:id/schedules"
          component={() => (
            <Schedule
              setBreadcrumb={() => {}}
              unifiedJobTemplate={unifiedJobTemplate}
            />
          )}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });
  afterAll(() => {
    wrapper.unmount();
  });
  test('renders successfully', async () => {
    expect(wrapper.length).toBe(1);
  });
  test('expect all tabs to exist, including Back to Schedules', async () => {
    expect(
      wrapper.find('button[link="/templates/job_template/1/schedules"]').length
    ).toBe(1);
    expect(wrapper.find('button[aria-label="Details"]').length).toBe(1);
  });
});
