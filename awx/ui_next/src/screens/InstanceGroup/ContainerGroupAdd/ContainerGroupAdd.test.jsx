import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InstanceGroupsAPI } from '../../../api';
import ContainerGroupAdd from './ContainerGroupAdd';

jest.mock('../../../api');

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

const instanceGroupCreateData = {
  name: 'Fuz',
  credential: { id: 71, name: 'CG' },
  pod_spec_override:
    'apiVersion: v1\nkind: Pod\nmetadata:\n  namespace: default\nspec:\n  containers:\n    - image: ansible/ansible-runner\n      tty: true\n      stdin: true\n      imagePullPolicy: Always\n      args:\n        - sleep\n        - infinity\n        - test',
};

InstanceGroupsAPI.create.mockResolvedValue({
  data: {
    id: 123,
  },
});

InstanceGroupsAPI.readOptions.mockResolvedValue({
  data: {
    results: initialPodSpec,
  },
});

describe('<ContainerGroupAdd/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/instance_groups'],
    });

    await act(async () => {
      wrapper = mountWithContexts(<ContainerGroupAdd />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('ContainerGroupForm').prop('onSubmit')({
        ...instanceGroupCreateData,
        override: true,
      });
    });
    wrapper.update();
    expect(InstanceGroupsAPI.create).toHaveBeenCalledWith({
      ...instanceGroupCreateData,
      credential: 71,
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toBe(
      '/instance_groups/container_group/123/details'
    );
  });

  test('handleCancel should return the user back to the instance group list', async () => {
    wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/instance_groups');
  });
});
