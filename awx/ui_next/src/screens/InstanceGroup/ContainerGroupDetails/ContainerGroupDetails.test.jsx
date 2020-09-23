import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InstanceGroupsAPI } from '../../../api';

import ContainerGroupDetails from './ContainerGroupDetails';

jest.mock('../../../api');

const instanceGroup = {
  id: 42,
  type: 'instance_group',
  url: '/api/v2/instance_groups/128/',
  related: {
    named_url: '/api/v2/instance_groups/A1/',
    jobs: '/api/v2/instance_groups/128/jobs/',
    instances: '/api/v2/instance_groups/128/instances/',
    credential: '/api/v2/credentials/71/',
  },
  name: 'Foo',
  created: '2020-09-03T18:26:47.113934Z',
  modified: '2020-09-03T19:34:23.244694Z',
  capacity: 0,
  committed_capacity: 0,
  consumed_capacity: 0,
  percent_capacity_remaining: 0.0,
  jobs_running: 0,
  jobs_total: 0,
  instances: 0,
  controller: null,
  is_controller: false,
  is_isolated: false,
  is_containerized: true,
  credential: 71,
  policy_instance_percentage: 0,
  policy_instance_minimum: 0,
  policy_instance_list: [],
  pod_spec_override:
    'apiVersion: v1\nkind: Pod\nmetadata:\n  namespace: default\nspec:\n  containers:\n    - image: ansible/ansible-runner\n      tty: true\n      stdin: true\n      imagePullPolicy: Always\n      args:\n        - sleep\n        - infinity\n        - test',
  summary_fields: {
    credential: {
      id: 71,
      name: 'CG',
      description: 'Container Group',
      kind: 'kubernetes_bearer_token',
      cloud: false,
      kubernetes: true,
      credential_type_id: 17,
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
};

describe('<ContainerGroupDetails/>', () => {
  let wrapper;
  test('should render details properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ContainerGroupDetails instanceGroup={instanceGroup} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Detail[label="Name"]').prop('value')).toEqual(
      instanceGroup.name
    );
    expect(wrapper.find('Detail[label="Type"]').prop('value')).toEqual(
      'Container group'
    );
    expect(
      wrapper.find('Detail[label="Credential"]').prop('value').props.children
    ).toEqual(instanceGroup.summary_fields.credential.name);
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      instanceGroup.pod_spec_override
    );
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(instanceGroup.created);
    expect(dates.at(1).prop('date')).toEqual(instanceGroup.modified);
  });

  test('expected api call is made for delete', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/credential_types/42/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ContainerGroupDetails instanceGroup={instanceGroup} />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(InstanceGroupsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(history.location.pathname).toBe('/instance_groups');
  });

  test('should not render delete button', async () => {
    instanceGroup.summary_fields.user_capabilities.delete = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <ContainerGroupDetails instanceGroup={instanceGroup} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(0);
  });

  test('should not render edit button', async () => {
    instanceGroup.summary_fields.user_capabilities.edit = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <ContainerGroupDetails instanceGroup={instanceGroup} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Edit"]').length).toBe(0);
  });
});
