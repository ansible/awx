import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import JobTemplateForm, { _JobTemplateForm } from './JobTemplateForm';
import { LabelsAPI } from '@api';

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
      labels: { results: [{ name: 'Sushi', id: 1 }, { name: 'Major', id: 2 }] },
    },
  };
  beforeEach(() => {
    LabelsAPI.read.mockReturnValue({
      data: mockData.summary_fields.labels,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
    const component = wrapper.find('ChipGroup');
    expect(LabelsAPI.read).toHaveBeenCalled();
    expect(component.find('span#pf-random-id-1').text()).toEqual('Sushi');
  });

  test('should update form values on input changes', async () => {
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );

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
    wrapper.find('InventoriesLookup').prop('onChange')({
      id: 3,
      name: 'inventory',
    });
    expect(form.state('values').inventory).toEqual(3);
    wrapper.find('input#template-project').simulate('change', {
      target: { value: 4, name: 'project' },
    });
    expect(form.state('values').project).toEqual(4);
    wrapper.find('input#template-playbook').simulate('change', {
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

    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toBeCalled();
  });

  test('should call handleCancel when Cancel button is clicked', () => {
    const handleCancel = jest.fn();
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={handleCancel}
      />
    );
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });

  test('handleNewLabel should arrange new labels properly', async () => {
    const handleNewLabel = jest.spyOn(
      _JobTemplateForm.prototype,
      'handleNewLabel'
    );
    const event = { key: 'Tab' };
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
    const multiSelect = wrapper.find('MultiSelect');
    const component = wrapper.find('JobTemplateForm');

    wrapper.setState({ newLabels: [], loadedLabels: [], removedLabels: [] });
    multiSelect.setState({ input: 'Foo' });
    component.find('input[aria-label="labels"]').prop('onKeyDown')(event);
    expect(handleNewLabel).toHaveBeenCalledWith('Foo');

    component.instance().handleNewLabel({ name: 'Bar', id: 2 });
    expect(component.state().newLabels).toEqual([
      { name: 'Foo', organization: 1 },
      { associate: true, id: 2, name: 'Bar' },
    ]);
  });
  test('disassociateLabel should arrange new labels properly', async () => {
    const wrapper = mountWithContexts(
      <JobTemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
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
