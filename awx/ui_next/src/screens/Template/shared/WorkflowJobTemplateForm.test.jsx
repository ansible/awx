import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { sleep } from '../../../../testUtils/testUtils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowJobTemplateForm from './WorkflowJobTemplateForm';
import {
  WorkflowJobTemplatesAPI,
  LabelsAPI,
  OrganizationsAPI,
  InventoriesAPI,
  ProjectsAPI,
  CredentialTypesAPI,
} from '../../../api';

jest.mock('../../../api/models/CredentialTypes');
jest.mock('../../../api/models/WorkflowJobTemplates');
jest.mock('../../../api/models/Labels');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/Projects');
jest.mock('../../../api/models/Credentials');

describe('<WorkflowJobTemplateForm/>', () => {
  let wrapper;
  let history;
  const handleSubmit = jest.fn();
  const handleCancel = jest.fn();
  const mockTemplate = {
    id: 6,
    name: 'Foo',
    description: 'Foo description',
    summary_fields: {
      inventory: { id: 1, name: 'Inventory 1' },
      organization: { id: 1, name: 'Organization 1' },
      labels: {
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
        ],
      },
    },
    scm_branch: 'devel',
    limit: '5000',
    variables: '---',
    related: {
      webhook_receiver: '/api/v2/workflow_job_templates/57/gitlab/',
    },
    webhook_credential: null,
    webhook_key: 'sdfghjklmnbvcdsew435678iokjhgfd',
    webhook_service: 'github',
  };

  beforeEach(async () => {
    WorkflowJobTemplatesAPI.updateWebhookKey.mockResolvedValue({
      data: { webhook_key: 'sdafdghjkl2345678ionbvcxz' },
    });
    LabelsAPI.read.mockResolvedValue({
      data: {
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
          { name: 'Label 3', id: 3 },
        ],
      },
    });
    OrganizationsAPI.read.mockResolvedValue({
      results: [{ id: 1 }, { id: 2 }],
    });
    InventoriesAPI.read.mockResolvedValue({
      results: [
        { id: 1, name: 'Foo' },
        { id: 2, name: 'Bar' },
      ],
    });
    CredentialTypesAPI.read.mockResolvedValue({
      data: { results: [{ id: 1 }] },
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });
    ProjectsAPI.readOptions.mockResolvedValue({
      data: { actions: { GET: {}, POST: {} } },
    });

    history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/6/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/workflow_job_template/:id/edit"
          component={() => (
            <WorkflowJobTemplateForm
              template={mockTemplate}
              handleCancel={handleCancel}
              handleSubmit={handleSubmit}
            />
          )}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 6 } },
              },
            },
          },
        }
      );
    });
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('all the fields render successfully', () => {
    const fields = [
      'FormField[name="name"]',
      'FormField[name="description"]',
      'FormGroup[label="Organization"]',
      'FieldWithPrompt[label="Inventory"]',
      'FieldWithPrompt[label="Limit"]',
      'FieldWithPrompt[label="Source control branch"]',
      'FormGroup[label="Labels"]',
      'VariablesField',
    ];

    const assertField = field => {
      expect(wrapper.find(`${field}`).length).toBe(1);
    };
    fields.map((field, index) => assertField(field, index));
  });

  test('changing inputs should update values', async () => {
    const inputsToChange = [
      {
        element: 'wfjt-name',
        value: { value: 'new foo', name: 'name' },
      },
      {
        element: 'wfjt-description',
        value: { value: 'new bar', name: 'description' },
      },
    ];
    const changeInputs = async ({ element, value }) => {
      wrapper.find(`input#${element}`).simulate('change', {
        target: { value: `${value.value}`, name: `${value.name}` },
      });
    };

    await act(async () => {
      inputsToChange.map(input => changeInputs(input));

      wrapper.find('LabelSelect').invoke('onChange')([
        { name: 'Label 3', id: 3 },
        { name: 'Label 1', id: 1 },
        { name: 'Label 2', id: 2 },
      ]);
      wrapper.find('InventoryLookup').invoke('onChange')({
        id: 3,
        name: 'inventory',
      });
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 3,
        name: 'organization',
      });
    });
    wrapper.update();

    const assertChanges = ({ element, value }) => {
      expect(wrapper.find(`input#${element}`).prop('value')).toEqual(
        `${value.value}`
      );
    };

    inputsToChange.map(input => assertChanges(input));
  });

  test('test changes in FieldWithPrompt', async () => {
    await act(async () => {
      wrapper.find('TextInputBase#text-wfjt-scm-branch').prop('onChange')(
        'main'
      );
      wrapper.find('TextInputBase#text-wfjt-limit').prop('onChange')(
        1234567890
      );
    });

    wrapper.update();

    expect(wrapper.find('input#text-wfjt-scm-branch').prop('value')).toEqual(
      'main'
    );
    expect(wrapper.find('input#text-wfjt-limit').prop('value')).toEqual(
      1234567890
    );
  });

  test('webhooks and enable concurrent jobs functions properly', async () => {
    act(() => {
      wrapper.find('Checkbox[aria-label="Enable Webhook"]').invoke('onChange')(
        true,
        {
          currentTarget: { value: true, type: 'change', checked: true },
        }
      );
    });
    wrapper.update();
    expect(
      wrapper.find('Checkbox[aria-label="Enable Webhook"]').prop('isChecked')
    ).toBe(true);
    expect(
      wrapper.find('input[aria-label="wfjt-webhook-key"]').prop('readOnly')
    ).toBe(true);
    expect(
      wrapper.find('input[aria-label="wfjt-webhook-key"]').prop('value')
    ).toBe('sdfghjklmnbvcdsew435678iokjhgfd');
    await act(() =>
      wrapper.find('Button[aria-label="Update webhook key"]').prop('onClick')()
    );
    expect(WorkflowJobTemplatesAPI.updateWebhookKey).toBeCalledWith('6');
    expect(
      wrapper.find('TextInputBase[aria-label="Webhook URL"]').prop('value')
    ).toContain('/api/v2/workflow_job_templates/57/gitlab/');
    wrapper.update();
    expect(wrapper.find('FormGroup[name="webhook_service"]').length).toBe(1);
    expect(wrapper.find('AnsibleSelect#webhook_service').length).toBe(1);
    await act(async () => {
      wrapper.find('AnsibleSelect#webhook_service').prop('onChange')(
        {},
        'gitlab'
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect#webhook_service').prop('value')).toBe(
      'gitlab'
    );
  });

  test('handleSubmit is called on submit button click', async () => {
    act(() => {
      wrapper.find('Formik').prop('onSubmit')({});
    });
    wrapper.update();
    sleep(0);
    expect(handleSubmit).toBeCalled();
  });

  test('handleCancel is called on cancel button click', async () => {
    act(() => {
      wrapper.find('button[aria-label="Cancel"]').simulate('click');
    });

    expect(handleCancel).toBeCalled();
  });
});
