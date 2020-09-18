import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { ExecutionEnvironmentsAPI } from '../../../api';

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
  created: '2020-09-17T20:14:15.408782Z',
  modified: '2020-09-17T20:14:15.408802Z',
  description: 'Foo',
  organization: null,
  image: 'https://localhost:90/12345/ma',
  managed_by_tower: false,
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
    expect(
      wrapper.find('Detail[label="Credential"]').prop('value').props.children
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
});
