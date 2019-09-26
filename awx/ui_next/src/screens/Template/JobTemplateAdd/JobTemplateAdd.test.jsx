import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import JobTemplateAdd from './JobTemplateAdd';
import { JobTemplatesAPI, LabelsAPI } from '@api';

jest.mock('@api');

const jobTemplateData = {
  name: 'Foo',
  description: 'Baz',
  job_type: 'run',
  inventory: 1,
  project: 2,
  playbook: 'Bar',
  forks: 0,
  limit: '',
  verbosity: '0',
  job_slice_count: 1,
  timeout: 0,
  job_tags: '',
  skip_tags: '',
  diff_mode: false,
  allow_callbacks: false,
  allow_simultaneous: false,
  use_fact_cache: false,
  host_config_key: '',
};

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
    expect(wrapper.find('InventoryLookup').prop('value')).toBe(null);
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
    expect(wrapper.find('PlaybookSelect')).toHaveLength(1);
    expect(wrapper.find('ProjectLookup').prop('value')).toBe(null);
    done();
  });

  test('handleSubmit should post to api', async done => {
    JobTemplatesAPI.create.mockResolvedValueOnce({
      data: {
        id: 1,
        ...jobTemplateData,
      },
    });
    const wrapper = mountWithContexts(<JobTemplateAdd />);
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      formik.setState(
        {
          values: jobTemplateData,
        },
        () => resolve()
      );
    });
    await changeState;
    wrapper.find('form').simulate('submit');
    await sleep(1);
    expect(JobTemplatesAPI.create).toHaveBeenCalledWith(jobTemplateData);
    done();
  });

  test('should navigate to job template detail after form submission', async done => {
    const history = {
      push: jest.fn(),
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

    await wrapper.find('JobTemplateForm').invoke('handleSubmit')(
      jobTemplateData
    );
    await sleep(0);
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
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(history.push).toHaveBeenCalledWith('/templates');
    done();
  });
});
