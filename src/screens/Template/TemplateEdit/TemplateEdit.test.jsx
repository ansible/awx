import React from 'react';
import { JobTemplatesAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import TemplateEdit from './TemplateEdit';

jest.mock('@api');

describe('<TemplateEdit />', () => {
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

  test('initially renders successfully', () => {
    mountWithContexts(
      <TemplateEdit
        template={mockData}
        hasPermissions
      />
    );
  });

  test('handleSubmit should call api update', () => {
    const wrapper = mountWithContexts(
      <TemplateEdit
        template={mockData}
        hasPermissions
      />
    );
    const updatedTemplateData = {
      name: 'new name',
      description: 'new description',
      job_type: 'check',
    };

    wrapper.find('TemplateForm').prop('handleSubmit')(updatedTemplateData);
    expect(JobTemplatesAPI.update).toHaveBeenCalledWith(1, updatedTemplateData);
  });

  test('should navigate to job template detail when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(
      <TemplateEdit
        template={mockData}
        hasPermissions
      />,
      { context: { router: { history } } }
    );

    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(history.push).toHaveBeenCalledWith('/templates/job_template/1/details');
  });
});
