import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { InstanceGroupsAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import InstanceGroupsLookup from './InstanceGroupsLookup';

jest.mock('../../api');

const mockedInstanceGroups = {
  count: 1,
  results: [
    {
      id: 2,
      name: 'Foo',
      image: 'quay.io/ansible/awx-ee',
      pull: 'missing',
    },
  ],
};

const instanceGroups = [
  {
    id: 1,
    type: 'instance_group',
    url: '/api/v2/instance_groups/1/',
    related: {
      jobs: '/api/v2/instance_groups/1/jobs/',
      instances: '/api/v2/instance_groups/1/instances/',
    },
    name: 'controlplane',
    created: '2022-09-13T15:44:54.870579Z',
    modified: '2022-09-13T15:44:54.886047Z',
    capacity: 59,
    consumed_capacity: 0,
    percent_capacity_remaining: 100.0,
    jobs_running: 0,
    jobs_total: 40,
    instances: 1,
    is_container_group: false,
    credential: null,
    policy_instance_percentage: 100,
    policy_instance_minimum: 0,
    policy_instance_list: [],
    pod_spec_override: '',
    summary_fields: {
      user_capabilities: {
        edit: true,
        delete: false,
      },
    },
  },
];

describe('InstanceGroupsLookup', () => {
  let wrapper;

  beforeEach(() => {
    InstanceGroupsAPI.read.mockResolvedValue({
      data: mockedInstanceGroups,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render successfully', async () => {
    InstanceGroupsAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <InstanceGroupsLookup value={instanceGroups} onChange={() => {}} />
        </Formik>
      );
    });
    wrapper.update();
    expect(InstanceGroupsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('InstanceGroupsLookup')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Instance Groups"]').length).toBe(1);
    expect(wrapper.find('Checkbox[aria-label="Prompt on launch"]').length).toBe(
      0
    );
  });
  test('should render prompt on launch checkbox when necessary', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <InstanceGroupsLookup
            value={instanceGroups}
            onChange={() => {}}
            isPromptableField
            promptId="ig-prompt"
            promptName="ask_instance_groups_on_launch"
          />
        </Formik>
      );
    });
    expect(wrapper.find('Checkbox[aria-label="Prompt on launch"]').length).toBe(
      1
    );
  });
});
