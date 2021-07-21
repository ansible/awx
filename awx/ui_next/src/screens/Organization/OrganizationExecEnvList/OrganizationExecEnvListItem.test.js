import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import OrganizationExecEnvListItem from './OrganizationExecEnvListItem';

describe('<OrganizationExecEnvListItem/>', () => {
  let wrapper;
  const executionEnvironment = {
    id: 1,
    image: 'https://registry.com/r/image/manifest',
    name: 'foo',
    organization: 1,
    credential: null,
    pull: 'always',
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <OrganizationExecEnvListItem
              executionEnvironment={executionEnvironment}
              detailUrl="execution_environments/1/details"
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('OrganizationExecEnvListItem').length).toBe(1);
  });

  test('should render the proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <OrganizationExecEnvListItem
              executionEnvironment={executionEnvironment}
              detailUrl="execution_environments/1/details"
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('Td').at(1).text()).toBe(executionEnvironment.image);
  });
});
