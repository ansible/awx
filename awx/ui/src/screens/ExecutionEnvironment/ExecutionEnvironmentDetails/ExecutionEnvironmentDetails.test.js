import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { ExecutionEnvironmentsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentDetails from './ExecutionEnvironmentDetails';

jest.mock('../../../api');

const executionEnvironment = {
  id: 17,
  type: 'execution_environment',
  url: '/api/v2/execution_environments/17/',
  related: {
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    activity_stream: '/api/v2/execution_environments/17/activity_stream/',
    unified_job_templates:
      '/api/v2/execution_environments/17/unified_job_templates/',
    credential: '/api/v2/credentials/4/',
  },
  summary_fields: {
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
    },
    credential: {
      id: 4,
      name: 'Container Registry',
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
  name: 'Default EE',
  created: '2020-09-17T20:14:15.408782Z',
  modified: '2020-09-17T20:14:15.408802Z',
  description: 'Foo',
  organization: null,
  image: 'https://localhost:90/12345/ma',
  managed: false,
  credential: 4,
};

describe('<ExecutionEnvironmentDetails/>', () => {
  let wrapper;
  test('should render details properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={executionEnvironment}
        />
      );
    });
    wrapper.update();

    expect(wrapper.find('Detail[label="Image"]').prop('value')).toEqual(
      executionEnvironment.image
    );
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toEqual(
      'Foo'
    );
    expect(wrapper.find('Detail[label="Organization"]').prop('value')).toEqual(
      'Globally Available'
    );
    expect(
      wrapper.find('Detail[label="Registry credential"]').prop('value').props
        .children
    ).toEqual(executionEnvironment.summary_fields.credential.name);
    expect(wrapper.find('Detail[label="Managed"]').prop('value')).toEqual(
      'False'
    );
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(executionEnvironment.created);
    expect(dates.at(1).prop('date')).toEqual(executionEnvironment.modified);
    const editButton = wrapper.find('Button[aria-label="edit"]');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/execution_environments/17/edit');

    const deleteButton = wrapper.find('Button[aria-label="Delete"]');
    expect(deleteButton.text()).toEqual('Delete');
  });

  test('should render organization detail', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={{
            ...executionEnvironment,
            organization: 1,
            summary_fields: {
              organization: { id: 1, name: 'Bar' },
              credential: {
                id: 4,
                name: 'Container Registry',
              },
            },
          }}
        />
      );
    });
    wrapper.update();

    expect(wrapper.find('Detail[label="Image"]').prop('value')).toEqual(
      executionEnvironment.image
    );
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toEqual(
      'Foo'
    );
    expect(wrapper.find(`Detail[label="Organization"] dd`).text()).toBe('Bar');
    expect(
      wrapper.find('Detail[label="Registry credential"]').prop('value').props
        .children
    ).toEqual(executionEnvironment.summary_fields.credential.name);
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(executionEnvironment.created);
    expect(dates.at(1).prop('date')).toEqual(executionEnvironment.modified);
  });

  test('expected api call is made for delete', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/execution_environments/42/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={executionEnvironment}
        />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(ExecutionEnvironmentsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(history.location.pathname).toBe('/execution_environments');
  });

  test('should render action buttons to managed ee', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={{
            ...executionEnvironment,
            managed: true,
          }}
        />
      );
    });
    wrapper.update();

    expect(wrapper.find('Detail[label="Image"]').prop('value')).toEqual(
      executionEnvironment.image
    );
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toEqual(
      'Foo'
    );
    expect(wrapper.find('Detail[label="Organization"]').prop('value')).toEqual(
      'Globally Available'
    );
    expect(
      wrapper.find('Detail[label="Registry credential"]').prop('value').props
        .children
    ).toEqual(executionEnvironment.summary_fields.credential.name);
    expect(wrapper.find('Detail[label="Managed"]').prop('value')).toEqual(
      'True'
    );
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(executionEnvironment.created);
    expect(dates.at(1).prop('date')).toEqual(executionEnvironment.modified);
    expect(wrapper.find('Button[aria-label="edit"]')).toHaveLength(1);

    expect(wrapper.find('Button[aria-label="Delete"]')).toHaveLength(1);
  });

  test('should have proper number of delete detail requests', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/execution_environments/42/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={executionEnvironment}
        />,
        {
          context: { router: { history } },
        }
      );
    });
    expect(
      wrapper.find('DeleteButton').prop('deleteDetailsRequests')
    ).toHaveLength(4);
  });

  test('should show edit button for users with edit permission', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={executionEnvironment}
        />
      );
    });
    const editButton = await waitForElement(
      wrapper,
      'ExecutionEnvironmentDetails Button[aria-label="edit"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/execution_environments/17/edit');
  });

  test('should hide edit button for users without edit permission', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={{
            ...executionEnvironment,
            summary_fields: { user_capabilities: { edit: false } },
          }}
        />
      );
    });
    await waitForElement(wrapper, 'ExecutionEnvironmentDetails');
    expect(
      wrapper.find('ExecutionEnvironmentDetails Button[aria-label="edit"]')
        .length
    ).toBe(0);
  });

  test('should show delete button for users with delete permission', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={executionEnvironment}
        />
      );
    });
    const deleteButton = await waitForElement(
      wrapper,
      'ExecutionEnvironmentDetails Button[aria-label="Delete"]'
    );
    expect(deleteButton.text()).toEqual('Delete');
  });

  test('should hide delete button for users without delete permission', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentDetails
          executionEnvironment={{
            ...executionEnvironment,
            summary_fields: { user_capabilities: { delete: false } },
          }}
        />
      );
    });
    await waitForElement(wrapper, 'ExecutionEnvironmentDetails');
    expect(
      wrapper.find('ExecutionEnvironmentDetails Button[aria-label="Delete"]')
        .length
    ).toBe(0);
  });
});
