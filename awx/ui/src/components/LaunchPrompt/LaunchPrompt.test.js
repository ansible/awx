import React from 'react';
import { act, isElementOfType } from 'react-dom/test-utils';
import {
  ExecutionEnvironmentsAPI,
  InstanceGroupsAPI,
  InventoriesAPI,
  CredentialsAPI,
  CredentialTypesAPI,
  JobTemplatesAPI,
} from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import LaunchPrompt from './LaunchPrompt';
import InventoryStep from './steps/InventoryStep';
import CredentialsStep from './steps/CredentialsStep';
import CredentialPasswordsStep from './steps/CredentialPasswordsStep';
import OtherPromptsStep from './steps/OtherPromptsStep';
import PreviewStep from './steps/PreviewStep';
import ExecutionEnvironmentStep from './steps/ExecutionEnvironmentStep';
import InstanceGroupsStep from './steps/InstanceGroupsStep';
import SurveyStep from './steps/SurveyStep';

jest.mock('../../api/models/Inventories');
jest.mock('../../api/models/ExecutionEnvironments');
jest.mock('../../api/models/CredentialTypes');
jest.mock('../../api/models/Credentials');
jest.mock('../../api/models/JobTemplates');
jest.mock('../../api/models/InstanceGroups');

let config;
const resource = {
  id: 1,
  description: 'Foo Description',
  name: 'Foobar',
  type: 'job_template',
  summary_fields: {
    credentials: [
      {
        id: 5,
        name: 'cred that prompts',
        credential_type: 1,
        inputs: {
          password: 'ASK',
        },
      },
    ],
  },
};
const noop = () => {};

describe('LaunchPrompt', () => {
  beforeEach(() => {
    InventoriesAPI.read.mockResolvedValue({
      data: {
        results: [{ id: 1, name: 'foo', url: '/inventories/1' }],
        count: 1,
      },
    });
    CredentialsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1 }], count: 1 },
    });
    CredentialTypesAPI.loadAllTypes({ data: { results: [{ type: 'ssh' }] } });
    JobTemplatesAPI.readSurvey.mockResolvedValue({
      data: {
        name: '',
        description: '',
        spec: [{ type: 'text', variable: 'foo' }],
      },
    });
    JobTemplatesAPI.readCredentials.mockResolvedValue({
      data: {
        results: [
          {
            id: 5,
            name: 'cred that prompts',
            credential_type: 1,
            inputs: {
              password: 'ASK',
            },
          },
        ],
      },
    });
    InstanceGroupsAPI.read.mockResolvedValue({
      data: {
        results: [
          {
            id: 2,
            type: 'instance_group',
            url: '/api/v2/instance_groups/2/',
            related: {
              jobs: '/api/v2/instance_groups/2/jobs/',
              instances: '/api/v2/instance_groups/2/instances/',
            },
            name: 'default',
            created: '2022-08-30T20:35:05.747132Z',
            modified: '2022-08-30T20:35:05.756690Z',
            capacity: 177,
            consumed_capacity: 0,
            percent_capacity_remaining: 100.0,
            jobs_running: 0,
            jobs_total: 2,
            instances: 3,
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
        ],
        count: 1,
      },
    });
    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: {
        results: [
          {
            id: 1,
            type: 'execution_environment',
            url: '/api/v2/execution_environments/1/',
            related: {
              activity_stream:
                '/api/v2/execution_environments/1/activity_stream/',
              unified_job_templates:
                '/api/v2/execution_environments/1/unified_job_templates/',
              copy: '/api/v2/execution_environments/1/copy/',
            },
            summary_fields: {
              execution_environment: {},
              user_capabilities: {
                edit: true,
                delete: true,
                copy: true,
              },
            },
            created: '2022-08-30T20:34:55.842997Z',
            modified: '2022-08-30T20:34:55.859874Z',
            name: 'AWX EE (latest)',
            description: '',
            organization: null,
            image: 'quay.io/ansible/awx-ee:latest',
            managed: false,
            credential: null,
            pull: '',
          },
        ],
        count: 1,
      },
    });

    config = {
      can_start_without_user_input: false,
      passwords_needed_to_start: [],
      ask_scm_branch_on_launch: false,
      ask_variables_on_launch: false,
      ask_tags_on_launch: false,
      ask_diff_mode_on_launch: false,
      ask_skip_tags_on_launch: false,
      ask_job_type_on_launch: false,
      ask_limit_on_launch: false,
      ask_verbosity_on_launch: false,
      ask_inventory_on_launch: false,
      ask_credential_on_launch: false,
      ask_execution_environment_on_launch: false,
      ask_labels_on_launch: false,
      ask_forks_on_launch: false,
      ask_job_slice_count_on_launch: false,
      ask_timeout_on_launch: false,
      ask_instance_groups_on_launch: false,
      survey_enabled: false,
      variables_needed_to_start: [],
      credential_needed_to_start: false,
      inventory_needed_to_start: false,
      job_template_data: { name: 'JT with prompts', id: 25, description: '' },
    };
  });

  afterEach(() => jest.clearAllMocks());

  test('should render Wizard with all steps', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            ask_inventory_on_launch: true,
            ask_credential_on_launch: true,
            ask_scm_branch_on_launch: true,
            ask_execution_environment_on_launch: true,
            ask_instance_groups_on_launch: true,
            survey_enabled: true,
            passwords_needed_to_start: ['ssh_password'],
            defaults: {
              credentials: [
                {
                  id: 1,
                  name: 'cred that prompts',
                  passwords_needed: ['ssh_password'],
                  credential_type: 1,
                },
              ],
            },
          }}
          resource={{
            ...resource,
            summary_fields: {
              credentials: [
                {
                  id: 5,
                  name: 'cred that prompts',
                  credential_type: 1,
                  inputs: {
                    password: 'ASK',
                  },
                },
              ],
            },
          }}
          resourceDefaultCredentials={[
            {
              id: 5,
              name: 'cred that prompts',
              credential_type: 1,
              inputs: {
                password: 'ASK',
              },
            },
          ]}
          onLaunch={noop}
          onCancel={noop}
          surveyConfig={{
            name: '',
            description: '',
            spec: [
              {
                choices: '',
                default: '',
                max: 1024,
                min: 0,
                new_question: false,
                question_description: '',
                question_name: 'foo',
                required: true,
                type: 'text',
                variable: 'foo',
              },
            ],
          }}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(8);
    expect(steps[0].name.props.children).toEqual('Inventory');
    expect(steps[1].name.props.children).toEqual('Credentials');
    expect(steps[2].name.props.children).toEqual('Credential passwords');
    expect(steps[3].name.props.children).toEqual('Execution Environment');
    expect(steps[4].name.props.children).toEqual('Instance Groups');
    expect(steps[5].name.props.children).toEqual('Other prompts');
    expect(steps[6].name.props.children).toEqual('Survey');
    expect(steps[7].name.props.children).toEqual('Preview');
    expect(wizard.find('WizardHeader').prop('title')).toBe('Launch | Foobar');
    expect(wizard.find('WizardHeader').prop('description')).toBe(
      'Foo Description'
    );
  });

  test('should add inventory step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            ask_inventory_on_launch: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(2);
    expect(steps[0].name.props.children).toEqual('Inventory');
    expect(isElementOfType(steps[0].component, InventoryStep)).toEqual(true);
    expect(isElementOfType(steps[1].component, PreviewStep)).toEqual(true);
  });

  test('should add credentials step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            ask_credential_on_launch: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
          resourceDefaultCredentials={[
            {
              id: 5,
              name: 'cred that prompts',
              credential_type: 1,
              inputs: {
                password: 'ASK',
              },
            },
          ]}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(3);
    expect(steps[0].name.props.children).toEqual('Credentials');
    expect(isElementOfType(steps[0].component, CredentialsStep)).toEqual(true);
    expect(
      isElementOfType(steps[1].component, CredentialPasswordsStep)
    ).toEqual(true);
    expect(isElementOfType(steps[2].component, PreviewStep)).toEqual(true);
  });

  test('should add execution environment step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            ask_execution_environment_on_launch: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(2);
    expect(steps[0].name.props.children).toEqual('Execution Environment');
    expect(
      isElementOfType(steps[0].component, ExecutionEnvironmentStep)
    ).toEqual(true);
    expect(isElementOfType(steps[1].component, PreviewStep)).toEqual(true);
  });

  test('should add instance groups step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            ask_instance_groups_on_launch: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(2);
    expect(steps[0].name.props.children).toEqual('Instance Groups');
    expect(isElementOfType(steps[0].component, InstanceGroupsStep)).toEqual(
      true
    );
    expect(isElementOfType(steps[1].component, PreviewStep)).toEqual(true);
  });

  test('should add other prompts step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            ask_verbosity_on_launch: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(2);
    expect(steps[0].name.props.children).toEqual('Other prompts');
    expect(isElementOfType(steps[0].component, OtherPromptsStep)).toEqual(true);
    expect(isElementOfType(steps[1].component, PreviewStep)).toEqual(true);
  });

  test('should add survey step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          launchConfig={{
            ...config,
            survey_enabled: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
          surveyConfig={{
            name: '',
            description: '',
            spec: [
              {
                choices: '',
                default: '',
                max: 1024,
                min: 0,
                new_question: false,
                question_description: '',
                question_name: 'foo',
                required: true,
                type: 'text',
                variable: 'foo',
              },
            ],
          }}
        />
      );
    });
    const wizard = await waitForElement(wrapper, 'Wizard');
    const steps = wizard.prop('steps');

    expect(steps).toHaveLength(2);
    expect(steps[0].name.props.children).toEqual('Survey');
    expect(isElementOfType(steps[0].component, SurveyStep)).toEqual(true);
    expect(isElementOfType(steps[1].component, PreviewStep)).toEqual(true);
  });
});
