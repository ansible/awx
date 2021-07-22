import React from 'react';
import { act } from 'react-dom/test-utils';

import { OrganizationsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import OrganizationExecEnvList from './OrganizationExecEnvList';

jest.mock('../../../api/');

const executionEnvironments = {
  data: {
    count: 3,
    results: [
      {
        id: 1,
        type: 'execution_environment',
        url: '/api/v2/execution_environments/1/',
        related: {
          organization: '/api/v2/organizations/1/',
        },
        organization: 1,
        image: 'https://localhost.com/image/disk',
        managed: false,
        credential: null,
      },
      {
        id: 2,
        type: 'execution_environment',
        url: '/api/v2/execution_environments/2/',
        related: {
          organization: '/api/v2/organizations/1/',
        },
        organization: 1,
        image: 'test/image123',
        managed: false,
        credential: null,
      },
      {
        id: 3,
        type: 'execution_environment',
        url: '/api/v2/execution_environments/3/',
        related: {
          organization: '/api/v2/organizations/1/',
        },
        organization: 1,
        image: 'test/test',
        managed: false,
        credential: null,
      },
    ],
  },
};

const mockOrganization = {
  id: 1,
  type: 'organization',
  name: 'Default',
};

const options = { data: { actions: { POST: {}, GET: {} } } };

describe('<OrganizationExecEnvList/>', () => {
  let wrapper;

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationExecEnvList organization={mockOrganization} />
      );
    });
    await waitForElement(
      wrapper,
      'OrganizationExecEnvList',
      (el) => el.length > 0
    );
  });

  test('should have data fetched and render 3 rows', async () => {
    OrganizationsAPI.readExecutionEnvironments.mockResolvedValue(
      executionEnvironments
    );

    OrganizationsAPI.readExecutionEnvironmentsOptions.mockResolvedValue(
      options
    );

    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationExecEnvList organization={mockOrganization} />
      );
    });
    await waitForElement(
      wrapper,
      'OrganizationExecEnvList',
      (el) => el.length > 0
    );

    expect(wrapper.find('OrganizationExecEnvListItem').length).toBe(3);
    expect(OrganizationsAPI.readExecutionEnvironments).toBeCalled();
    expect(OrganizationsAPI.readExecutionEnvironmentsOptions).toBeCalled();
  });

  test('should not render add button', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationExecEnvList organization={mockOrganization} />
      );
    });
    waitForElement(wrapper, 'OrganizationExecEnvList', (el) => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
