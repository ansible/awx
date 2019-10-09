import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
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

  test('should render Job Template Form', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobTemplateAdd />);
    });
    expect(wrapper.find('JobTemplateForm').length).toBe(1);
  });

  test('should render Job Template Form with default values', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobTemplateAdd />);
    });
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
  });

  test('handleSubmit should post to api', async () => {
    JobTemplatesAPI.create.mockResolvedValueOnce({
      data: {
        id: 1,
        ...jobTemplateData,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobTemplateAdd />);
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      formik.setState(
        {
          values: {
            ...jobTemplateData,
            labels: [],
            instanceGroups: [],
          },
        },
        () => resolve()
      );
    });
    await changeState;
    wrapper.find('form').simulate('submit');
    await sleep(1);
    expect(JobTemplatesAPI.create).toHaveBeenCalledWith(jobTemplateData);
  });

  test('should navigate to job template detail after form submission', async () => {
    const history = createMemoryHistory({});
    JobTemplatesAPI.create.mockResolvedValueOnce({
      data: {
        id: 1,
        type: 'job_template',
        ...jobTemplateData,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobTemplateAdd />, {
        context: { router: { history } },
      });
    });

    const updatedTemplateData = {
      name: 'new name',
      description: 'new description',
      job_type: 'check',
    };
    const labels = [
      { id: 3, name: 'Foo', isNew: true },
      { id: 4, name: 'Bar', isNew: true },
      { id: 5, name: 'Maple' },
      { id: 6, name: 'Tree' },
    ];
    JobTemplatesAPI.update.mockResolvedValue({
      data: { ...updatedTemplateData },
    });
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      const values = {
        ...jobTemplateData,
        ...updatedTemplateData,
        labels,
        instanceGroups: [],
      };
      formik.setState({ values }, () => resolve());
    });
    await changeState;
    await wrapper.find('JobTemplateForm').invoke('handleSubmit')(
      jobTemplateData
    );
    await sleep(0);
    expect(history.location.pathname).toEqual(
      '/templates/job_template/1/details'
    );
  });

  test('should navigate to templates list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobTemplateAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(history.location.pathname).toEqual('/templates');
  });
});
