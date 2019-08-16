import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import JobTemplateAdd from './JobTemplateAdd';
import { JobTemplatesAPI, LabelsAPI } from '@api';

jest.mock('@api');

describe('<JobTemplateAdd />', () => {
  const defaultProps = {
    description: '',
    inventory: '',
    job_type: 'run',
    name: '',
    playbook: '',
    project: '',
    summary_fields: {
      user_capabilities: {
        edit: true,
      },
    },
  };

  beforeEach(() => {
    LabelsAPI.read.mockResolvedValue({ data: { results: [] } });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render Job Template Form', () => {
    const wrapper = mountWithContexts(<JobTemplateAdd />);
    expect(wrapper.find('JobTemplateForm').length).toBe(1);
  });

  test('should render Job Template Form with default values', async done => {
    const wrapper = mountWithContexts(<JobTemplateAdd />);
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    expect(wrapper.find('input#template-description').text()).toBe(
      defaultProps.description
    );
    expect(wrapper.find('InventoriesLookup').prop('value')).toBe(null);
    expect(wrapper.find('AnsibleSelect[name="job_type"]').props().value).toBe(
      defaultProps.job_type
    );
    expect(
      wrapper
        .find('AnsibleSelect[name="job_type"]')
        .containsAllMatchingElements([
          <option>Choose a job type</option>,
          <option>Run</option>,
          <option>Check</option>,
        ])
    ).toEqual(true);

    expect(wrapper.find('input#template-name').text()).toBe(defaultProps.name);
    expect(wrapper.find('input#template-playbook').text()).toBe(
      defaultProps.playbook
    );
    expect(wrapper.find('ProjectLookup').prop('value')).toBe(null);
    done();
  });

  test('handleSubmit should post to api', async done => {
    const jobTemplateData = {
      description: 'Baz',
      inventory: 1,
      job_type: 'run',
      name: 'Foo',
      playbook: 'Bar',
      project: 2,
    };
    JobTemplatesAPI.create.mockResolvedValueOnce({
      data: {
        id: 1,
        ...jobTemplateData,
      },
    });
    const wrapper = mountWithContexts(<JobTemplateAdd />);
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper.find('JobTemplateForm').prop('handleSubmit')(jobTemplateData);
    expect(JobTemplatesAPI.create).toHaveBeenCalledWith(jobTemplateData);
    done();
  });

  test('should navigate to job template detail after form submission', async done => {
    const history = {
      push: jest.fn(),
    };
    const jobTemplateData = {
      description: 'Baz',
      inventory: 1,
      job_type: 'run',
      name: 'Foo',
      playbook: 'Bar',
      project: 2,
    };
    JobTemplatesAPI.create.mockResolvedValueOnce({
      data: {
        id: 1,
        type: 'job_template',
        ...jobTemplateData,
      },
    });
    const wrapper = mountWithContexts(<JobTemplateAdd />, {
      context: { router: { history } },
    });

    await wrapper.find('JobTemplateForm').prop('handleSubmit')(jobTemplateData);
    expect(history.push).toHaveBeenCalledWith(
      '/templates/job_template/1/details'
    );
    done();
  });

  test('should navigate to templates list when cancel is clicked', async done => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(<JobTemplateAdd />, {
      context: { router: { history } },
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(history.push).toHaveBeenCalledWith('/templates');
    done();
  });
});
