import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import TemplateForm from './TemplateForm';

jest.mock('@api');

describe('<TemplateForm />', () => {
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    job_type: 'run',
    inventory: 2,
    project: 3,
    playbook: 'Baz',
    type: 'job_template'
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <TemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );
  });

  test('should update form values on input changes', () => {
    const wrapper = mountWithContexts(
      <TemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
      />
    );

    const form = wrapper.find('Formik');
    wrapper.find('input#template-name').simulate('change', {
      target: { value: 'new foo', name: 'name' }
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#template-description').simulate('change', {
      target: { value: 'new bar', name: 'description' }
    });
    expect(form.state('values').description).toEqual('new bar');
    wrapper.find('AnsibleSelect[name="job_type"]').simulate('change', {
      target: { value: 'new job type', name: 'job_type' }
    });
    expect(form.state('values').job_type).toEqual('new job type');
    wrapper.find('input#template-inventory').simulate('change', {
      target: { value: 3, name: 'inventory' }
    });
    expect(form.state('values').inventory).toEqual(3);
    wrapper.find('input#template-project').simulate('change', {
      target: { value: 4, name: 'project' }
    });
    expect(form.state('values').project).toEqual(4);
    wrapper.find('input#template-playbook').simulate('change', {
      target: { value: 'new baz type', name: 'playbook' }
    });
    expect(form.state('values').playbook).toEqual('new baz type');
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <TemplateForm
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
      <TemplateForm
        template={mockData}
        handleSubmit={jest.fn()}
        handleCancel={handleCancel}
      />
    );
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
