import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ManagementJobListItem from './ManagementJobListItem';

describe('<ManagementJobListItem/>', () => {
  let wrapper;

  const managementJob = {
    id: 3,
    name: 'Cleanup Expired Sessions',
    description: 'Cleans out expired browser sessions',
    job_type: 'cleanup_sessions',
    url: '/api/v2/system_job_templates/3/',
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ManagementJobListItem
              id={managementJob.id}
              name={managementJob.name}
              description={managementJob.description}
              isSuperUser
              onLaunchError={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('ManagementJobListItem').length).toBe(1);
  });

  test('should render the proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ManagementJobListItem
              id={managementJob.id}
              name={managementJob.name}
              description={managementJob.description}
              isSuperUser
              onLaunchError={() => {}}
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('Td').at(1).text()).toBe(managementJob.name);
    expect(wrapper.find('Td').at(2).text()).toBe(managementJob.description);

    expect(wrapper.find('RocketIcon').exists()).toBeTruthy();
  });
});
