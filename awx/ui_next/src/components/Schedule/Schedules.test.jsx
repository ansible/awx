import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import Schedules from './Schedules';

describe('<Schedules />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/schedules'],
    });
    const jobTemplate = { id: 1, name: 'Mock JT' };

    await act(async () => {
      wrapper = mountWithContexts(
        <Schedules
          setBreadcrumb={() => {}}
          jobTemplate={jobTemplate}
          loadSchedules={() => {}}
          loadScheduleOptions={() => {}}
        />,

        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    expect(wrapper.length).toBe(1);
  });
});
