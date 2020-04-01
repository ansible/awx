import React from 'react';
import { act, isElementOfType } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import LaunchPrompt from './LaunchPrompt';
import InventoryStep from './InventoryStep';
import PreviewStep from './PreviewStep';
import { InventoriesAPI } from '@api';

jest.mock('@api/models/Inventories');

let config;
const resource = {
  id: 1,
  type: 'job_template',
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
          config={{
            ...config,
            ask_inventory_on_launch: true,
            ask_credential_on_launch: true,
            ask_scm_branch_on_launch: true,
            survey_enabled: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
        />
      );
    });
    const steps = wrapper.find('Wizard').prop('steps');

    expect(steps).toHaveLength(5);
    expect(steps[0].name).toEqual('Inventory');
    expect(steps[1].name).toEqual('Credential');
    expect(steps[2].name).toEqual('Other Prompts');
    expect(steps[3].name).toEqual('Survey');
    expect(steps[4].name).toEqual('Preview');
  });

  test('should add inventory step', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LaunchPrompt
          config={{
            ...config,
            ask_inventory_on_launch: true,
          }}
          resource={resource}
          onLaunch={noop}
          onCancel={noop}
        />
      );
    });
    const steps = wrapper.find('Wizard').prop('steps');

    expect(steps).toHaveLength(2);
    expect(steps[0].name).toEqual('Inventory');
    expect(isElementOfType(steps[0].component, InventoryStep)).toEqual(true);
    expect(isElementOfType(steps[1].component, PreviewStep)).toEqual(true);
  });
});
