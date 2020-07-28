import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import JobTemplateAdd from './JobTemplateAdd';
import {
  CredentialsAPI,
  CredentialTypesAPI,
  JobTemplatesAPI,
  LabelsAPI,
  ProjectsAPI,
} from '../../../api';

jest.mock('../../../api');
CredentialsAPI.read.mockResolvedValue({
  data: {
    results: [],
    count: 0,
  },
});
CredentialTypesAPI.loadAllTypes.mockResolvedValue([]);
ProjectsAPI.readPlaybooks.mockResolvedValue({
  data: [],
});

const jobTemplateData = {
  allow_callbacks: false,
  allow_simultaneous: false,
  ask_credential_on_launch: false,
  ask_diff_mode_on_launch: false,
  ask_inventory_on_launch: false,
  ask_job_type_on_launch: false,
  ask_limit_on_launch: false,
  ask_scm_branch_on_launch: false,
  ask_skip_tags_on_launch: false,
  ask_tags_on_launch: false,
  ask_variables_on_launch: false,
  ask_verbosity_on_launch: false,
  become_enabled: false,
  description: '',
  diff_mode: false,
  extra_vars: '---\n',
  forks: 0,
  host_config_key: '',
  inventory: 1,
  job_slice_count: 1,
  job_tags: '',
  job_type: 'run',
  limit: '',
  name: '',
  playbook: '',
  project: { id: 1, summary_fields: { organization: { id: 1 } } },
  scm_branch: '',
  skip_tags: '',
  timeout: 0,
  use_fact_cache: false,
  verbosity: '0',
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
    act(() => {
      wrapper.find('input#template-name').simulate('change', {
        target: { value: 'Bar', name: 'name' },
      });
      wrapper.find('AnsibleSelect#template-job-type').prop('onChange')(
        null,
        'check'
      );
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 2,
        name: 'project',
        summary_fields: { organization: { id: 1, name: 'Org Foo' } },
      });
      wrapper.update();
      wrapper
        .find('PlaybookSelect')
        .prop('field')
        .onChange({
          target: { value: 'Baz', name: 'playbook' },
        });
    });
    wrapper.update();
    act(() => {
      wrapper.find('InventoryLookup').invoke('onChange')({
        id: 2,
        organization: 1,
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    wrapper.update();
    expect(JobTemplatesAPI.create).toHaveBeenCalledWith({
      ...jobTemplateData,
      name: 'Bar',
      job_type: 'check',
      project: 2,
      playbook: 'Baz',
      inventory: 2,
      webhook_credential: undefined,
      webhook_service: '',
    });
  });

  test('should navigate to job template detail after form submission', async () => {
    const history = createMemoryHistory({});
    JobTemplatesAPI.create.mockResolvedValueOnce({
      data: {
        id: 1,
        type: 'job_template',
        ...jobTemplateData,
        project: jobTemplateData.project.id,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobTemplateAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    act(() => {
      wrapper.find('input#template-name').simulate('change', {
        target: { value: 'Foo', name: 'name' },
      });
      wrapper.find('AnsibleSelect#template-job-type').prop('onChange')(
        null,
        'check'
      );
      wrapper.find('ProjectLookup').invoke('onChange')({
        id: 2,
        name: 'project',
        summary_fields: { organization: { id: 1, name: 'Org Foo' } },
      });
      wrapper.update();
      wrapper
        .find('PlaybookSelect')
        .prop('field')
        .onChange({
          target: { value: 'Bar', name: 'playbook' },
        });
    });
    wrapper.update();
    act(() => {
      wrapper.find('InventoryLookup').invoke('onChange')({
        id: 1,
        organization: 1,
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    wrapper.update();

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
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/templates');
  });
});
