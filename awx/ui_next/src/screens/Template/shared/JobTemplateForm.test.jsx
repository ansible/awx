import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import JobTemplateForm, { _JobTemplateForm } from './JobTemplateForm';
import { LabelsAPI, JobTemplatesAPI, ProjectsAPI } from '@api';

jest.mock('@api');

describe('<JobTemplateForm />', () => {
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    job_type: 'run',
    inventory: 2,
    project: 3,
    playbook: 'Baz',
    type: 'job_template',
    summary_fields: {
      inventory: {
        id: 2,
        name: 'foo',
        organization_id: 1,
      },
      project: {
        id: 3,
        name: 'qux',
      },
      labels: { results: [{ name: 'Sushi', id: 1 }, { name: 'Major', id: 2 }] },
    },
  };
  const mockInstanceGroups = [
    {
      id: 1,
      type: 'instance_group',
      url: '/api/v2/instance_groups/1/',
      related: {
        jobs: '/api/v2/instance_groups/1/jobs/',
        instances: '/api/v2/instance_groups/1/instances/',
      },
      name: 'tower',
      capacity: 59,
      committed_capacity: 0,
      consumed_capacity: 0,
      percent_capacity_remaining: 100.0,
      jobs_running: 0,
      jobs_total: 3,
      instances: 1,
      controller: null,
      is_controller: false,
      is_isolated: false,
      policy_instance_percentage: 100,
      policy_instance_minimum: 0,
      policy_instance_list: [],
    },
  ];
  beforeEach(() => {
    LabelsAPI.read.mockReturnValue({
      data: mockData.summary_fields.labels,
    });
    JobTemplatesAPI.readInstanceGroups.mockReturnValue({
      data: { results: mockInstanceGroups },
    });
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml'],
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render labels MultiSelect', async () => {
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
    await waitForElement(wrapper, 'Form', el => el.length === 0);
    expect(LabelsAPI.read).toHaveBeenCalled();
    expect(JobTemplatesAPI.readInstanceGroups).toHaveBeenCalled();
    wrapper.update();
    expect(
      wrapper
        .find('FormGroup[fieldId="template-labels"] MultiSelect')
        .prop('associatedItems')
    ).toEqual(mockData.summary_fields.labels.results);
  });

  test('should update form values on input changes', async () => {
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );

    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const form = wrapper.find('Formik');
    wrapper.find('input#template-name').simulate('change', {
      target: { value: 'new foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#template-description').simulate('change', {
      target: { value: 'new bar', name: 'description' },
    });
    expect(form.state('values').description).toEqual('new bar');
    wrapper.find('AnsibleSelect[name="job_type"]').simulate('change', {
      target: { value: 'new job type', name: 'job_type' },
    });
    expect(form.state('values').job_type).toEqual('new job type');
    wrapper.find('InventoryLookup').prop('onChange')({
      id: 3,
      name: 'inventory',
    });
    expect(form.state('values').inventory).toEqual(3);
    wrapper.find('ProjectLookup').prop('onChange')({
      id: 4,
      name: 'project',
    });
    expect(form.state('values').project).toEqual(4);
    wrapper.find('AnsibleSelect[name="playbook"]').simulate('change', {
      target: { value: 'new baz type', name: 'playbook' },
    });
    expect(form.state('values').playbook).toEqual('new baz type');
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
      />
    );
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toBeCalled();
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    const handleCancel = jest.fn();
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={handleCancel}
      />
    );
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });

  // TODO Move this test to <LabelSelect> tests
  test.skip('handleNewLabel should arrange new labels properly', async () => {
    const event = { key: 'Enter', preventDefault: () => {} };
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const multiSelect = wrapper.find(
      'FormGroup[fieldId="template-labels"] MultiSelect'
    );
    const component = wrapper.find('JobTemplateForm');

    wrapper.setState({ newLabels: [], loadedLabels: [], removedLabels: [] });
    multiSelect.setState({ input: 'Foo' });
    component
      .find('FormGroup[fieldId="template-labels"] input[aria-label="labels"]')
      .prop('onKeyDown')(event);

    component.instance().handleNewLabel({ name: 'Bar', id: 2 });
    const newLabels = component.state('newLabels');
    expect(newLabels).toHaveLength(2);
    expect(newLabels[0].name).toEqual('Foo');
    expect(newLabels[0].organization).toEqual(1);
  });

  // TODO Move this test to <LabelSelect> tests
  test.skip('disassociateLabel should arrange new labels properly', async () => {
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const component = wrapper.find('JobTemplateForm');
    // This asserts that the user generated a label or clicked
    // on a label option, and then changed their mind and
    // removed the label.
    component.instance().removeLabel({ name: 'Alex', id: 17 });
    expect(component.state().newLabels.length).toBe(0);
    expect(component.state().removedLabels.length).toBe(0);
    // This asserts that the user removed a label that was associated
    // with the template when the template loaded.
    component.instance().removeLabel({ name: 'Sushi', id: 1 });
    expect(component.state().newLabels.length).toBe(0);
    expect(component.state().removedLabels.length).toBe(1);
  });
});
