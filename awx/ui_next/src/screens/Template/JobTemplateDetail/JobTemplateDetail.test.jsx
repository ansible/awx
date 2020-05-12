import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import JobTemplateDetail from './JobTemplateDetail';
import { JobTemplatesAPI } from '../../../api';
import mockTemplate from '../shared/data.job_template.json';

jest.mock('../../../api');

const mockInstanceGroups = {
  count: 5,
  data: {
    results: [
      { id: 1, name: 'IG1' },
      { id: 2, name: 'IG2' },
    ],
  },
};

describe('<JobTemplateDetail />', () => {
  let wrapper;

  beforeEach(async () => {
    JobTemplatesAPI.readInstanceGroups.mockResolvedValue(mockInstanceGroups);
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateDetail template={mockTemplate} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });
  test('should render successfully with missing summary fields', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateDetail
          template={{
            ...mockTemplate,
            become_enabled: true,
            summary_fields: { user_capabilities: {} },
          }}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(
      wrapper,
      'Detail[label="Name"]',
      el => el.length === 1
    );
  });

  test('should request instance groups from api', async () => {
    expect(JobTemplatesAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('should hide edit button for users without edit permission', async () => {
    JobTemplatesAPI.readInstanceGroups.mockResolvedValue({ data: {} });
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateDetail
          template={{
            ...mockTemplate,
            diff_mode: true,
            host_config_key: 'key',
            summary_fields: { user_capabilities: { edit: false } },
          }}
        />
      );
    });
    expect(wrapper.find('button[aria-label="Edit"]').length).toBe(0);
  });

  test('should render credential chips', () => {
    const chips = wrapper.find('CredentialChip');
    expect(chips).toHaveLength(2);
    chips.forEach((chip, id) => {
      expect(chip.prop('credential')).toEqual(
        mockTemplate.summary_fields.credentials[id]
      );
    });
  });

  test('should render Source Control Branch', async () => {
    const SCMBranch = wrapper.find('Detail[label="Source Control Branch"]');
    expect(SCMBranch.prop('value')).toBe('Foo branch');
  });

  test('should show content error for failed instance group fetch', async () => {
    JobTemplatesAPI.readInstanceGroups.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <JobTemplateDetail
          template={{
            ...mockTemplate,
            allow_simultaneous: true,
            ask_inventory_on_launch: true,
            summary_fields: {
              inventory: {
                kind: 'smart',
              },
            },
          }}
        />
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('expected api calls are made for delete', async () => {
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(JobTemplatesAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('Error dialog shown for failed deletion', async () => {
    JobTemplatesAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 0
    );
  });
  test('webhook fields should render properly', () => {
    expect(wrapper.find('Detail[label="Webhook Service"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Webhook Service"]').prop('value')).toBe(
      'GitHub'
    );
    expect(wrapper.find('Detail[label="Webhook URL"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Webhook URL"]').prop('value')).toContain(
      'api/v2/job_templates/7/github/'
    );
    expect(wrapper.find('Detail[label="Webhook Key"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Webhook Credential"]').length).toBe(1);
  });
});
