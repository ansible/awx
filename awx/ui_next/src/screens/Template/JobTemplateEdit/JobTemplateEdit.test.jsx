import React from 'react';
import { JobTemplatesAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import JobTemplateEdit from './JobTemplateEdit';

jest.mock('@api');

describe('<JobTemplateEdit />', () => {
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
      user_capabilities: {
        edit: true,
      },
    },
  };

  test('initially renders successfully', () => {
    mountWithContexts(<JobTemplateEdit template={mockData} />);
  });

  test('handleSubmit should call api update', () => {
    const wrapper = mountWithContexts(<JobTemplateEdit template={mockData} />);
    const updatedTemplateData = {
      name: 'new name',
      description: 'new description',
      job_type: 'check',
    };

    wrapper.find('JobTemplateForm').prop('handleSubmit')(updatedTemplateData);
    expect(JobTemplatesAPI.update).toHaveBeenCalledWith(1, updatedTemplateData);
  });

  test('should navigate to job template detail when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(<JobTemplateEdit template={mockData} />, {
      context: { router: { history } },
    });

    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(history.push).toHaveBeenCalledWith(
      '/templates/job_template/1/details'
    );
  });
});
