import React from 'react';
import { act, isElementOfType } from 'react-dom/test-utils';
import {
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
import executionEnvironmentHelpTextStrings from 'screens/ExecutionEnvironment/shared/ExecutionEnvironment.helptext';
import { ExecutionEnvironment } from 'types';
import ExecutionEnvironmentStep from './steps/ExecutionEnvironmentStep';

jest.mock('../../api/models/Inventories');
jest.mock('../../api/models/ExecutionEnvironments');
jest.mock('../../api/models/CredentialTypes');
jest.mock('../../api/models/Credentials');
jest.mock('../../api/models/JobTemplates');

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

    expect(steps).toHaveLength(7);
    expect(steps[0].name.props.children).toEqual('Inventory');
    expect(steps[1].name.props.children).toEqual('Credentials');
    expect(steps[2].name.props.children).toEqual('Credential passwords');
    expect(steps[3].name.props.children).toEqual('Execution Environment');
    expect(steps[4].name.props.children).toEqual('Other prompts');
    expect(steps[5].name.props.children).toEqual('Survey');
    expect(steps[6].name.props.children).toEqual('Preview');
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
});
