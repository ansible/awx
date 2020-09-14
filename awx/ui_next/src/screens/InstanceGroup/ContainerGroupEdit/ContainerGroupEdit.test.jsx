import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InstanceGroupsAPI, CredentialsAPI } from '../../../api';
import ContainerGroupEdit from './ContainerGroupEdit';

jest.mock('../../../api');

const instanceGroup = {
  id: 123,
  type: 'instance_group',
  url: '/api/v2/instance_groups/123/',
  related: {
    named_url: '/api/v2/instance_groups/Foo/',
    jobs: '/api/v2/instance_groups/123/jobs/',
    instances: '/api/v2/instance_groups/123/instances/',
    credential: '/api/v2/credentials/71/',
  },
  name: 'Foo',
  created: '2020-09-02T17:20:01.214170Z',
  modified: '2020-09-02T17:20:01.214236Z',
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
  pod_spec_override: '',
  summary_fields: {
    credential: {
      id: 71,
      name: 'CG',
      description: 'a',
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

const updatedInstanceGroup = {
  name: 'Bar',
  credential: { id: 12, name: 'CGX' },
};

const initialPodSpec = {
  default: {
    apiVersion: 'v1',
    kind: 'Pod',
    metadata: {
      namespace: 'default',
    },
    spec: {
      containers: [
        {
          image: 'ansible/ansible-runner',
          tty: true,
          stdin: true,
          imagePullPolicy: 'Always',
          args: ['sleep', 'infinity'],
        },
      ],
    },
  },
};

InstanceGroupsAPI.readOptions.mockResolvedValue({
  data: {
    results: initialPodSpec,
  },
});

CredentialsAPI.read.mockResolvedValue({
  data: {
    results: [
      {
        id: 71,
        name: 'Test',
      },
    ],
  },
});

describe('<ContainerGroupEdit/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({ initialEntries: ['/instance_groups'] });
    await act(async () => {
      wrapper = mountWithContexts(
        <ContainerGroupEdit instanceGroup={instanceGroup} />,
        {
          context: { router: { history } },
        }
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders successfully', async () => {
    expect(wrapper.find('ContainerGroupEdit').length).toBe(1);
  });

  test('called InstanceGroupsAPI.readOptions', async () => {
    expect(InstanceGroupsAPI.readOptions).toHaveBeenCalledTimes(1);
  });

  test('handleCancel returns the user to container group detail', async () => {
    await act(async () => {
      wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual(
      '/instance_groups/container_group/123/details'
    );
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('ContainerGroupForm').prop('onSubmit')({
        ...updatedInstanceGroup,
        override: false,
      });
    });
    wrapper.update();
    expect(InstanceGroupsAPI.update).toHaveBeenCalledWith(123, {
      ...updatedInstanceGroup,
      credential: 12,
      pod_spec_override: null,
    });
    expect(history.location.pathname).toEqual(
      '/instance_groups/container_group/123/details'
    );
  });
});
