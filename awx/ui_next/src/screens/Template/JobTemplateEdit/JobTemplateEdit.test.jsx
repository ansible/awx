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
      labels: {
        results: [{ name: 'Sushi', id: 1 }, { name: 'Major', id: 2 }],
      },
    },
  };

  test('initially renders successfully', () => {
    mountWithContexts(<JobTemplateEdit template={mockData} />);
  });

  test('handleSubmit should call api update', async (done) => {
    const wrapper = mountWithContexts(<JobTemplateEdit template={mockData} />);
    const updatedTemplateData = {
      name: 'new name',
      description: 'new description',
      job_type: 'check',
    };
    const newLabels = [
      { associate: true, id: 3 },
      { associate: true, id: 3 },
      { name: 'Mapel', organization: 1 },
      { name: 'Tree', organization: 1 },
    ];
    const removedLabels = [
      { disassociate: true, id: 1 },
      { disassociate: true, id: 2 },
    ];

    await wrapper.find('JobTemplateForm').prop('handleSubmit')(
      updatedTemplateData,
      newLabels,
      removedLabels
    );
    expect(JobTemplatesAPI.update).toHaveBeenCalledWith(1, updatedTemplateData);
    expect(JobTemplatesAPI.disassociateLabel).toHaveBeenCalledTimes(2);
    expect(JobTemplatesAPI.associateLabel).toHaveBeenCalledTimes(2);
    expect(JobTemplatesAPI.generateLabel).toHaveBeenCalledTimes(2);
    done();
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
