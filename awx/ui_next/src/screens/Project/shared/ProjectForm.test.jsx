import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import ProjectForm from './ProjectForm';
import { CredentialTypesAPI, ProjectsAPI } from '../../../api';

jest.mock('../../../api');

describe('<ProjectForm />', () => {
  let wrapper;
  const mockData = {
    name: 'foo',
    description: 'bar',
    scm_type: 'git',
    scm_url: 'https://foo.bar',
    scm_clean: true,
    credential: 100,
    organization: 2,
    scm_update_on_launch: true,
    scm_update_cache_timeout: 3,
    allow_override: false,
    custom_virtualenv: '/venv/custom-env',
    summary_fields: {
      credential: {
        id: 100,
        credential_type_id: 4,
        kind: 'scm',
        name: 'Foo',
      },
      organization: {
        id: 2,
        name: 'Default',
      },
    },
  };

  const projectOptionsResolve = {
    data: {
      actions: {
        GET: {
          scm_type: {
            choices: [
              ['', 'Manual'],
              ['git', 'Git'],
              ['hg', 'Mercurial'],
              ['svn', 'Subversion'],
              ['archive', 'Remote Archive'],
              ['insights', 'Red Hat Insights'],
            ],
          },
        },
      },
    },
  };

  const scmCredentialResolve = {
    data: {
      results: [
        {
          id: 4,
          name: 'Source Control',
          kind: 'scm',
        },
      ],
    },
  };

  const insightsCredentialResolve = {
    data: {
      results: [
        {
          id: 5,
          name: 'Insights',
          kind: 'insights',
        },
      ],
    },
  };

  beforeEach(async () => {
    await ProjectsAPI.readOptions.mockImplementation(
      () => projectOptionsResolve
    );
    await CredentialTypesAPI.read.mockImplementationOnce(
      () => scmCredentialResolve
    );
    await CredentialTypesAPI.read.mockImplementationOnce(
      () => insightsCredentialResolve
    );
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });

    expect(wrapper.find('ProjectForm').length).toBe(1);
  });

  test('new form displays primary form fields', async () => {
    const config = {
      custom_virtualenvs: ['venv/foo', 'venv/bar'],
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Source Control Credential Type"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="Ansible Environment"]').length).toBe(
      1
    );
    expect(wrapper.find('FormGroup[label="Options"]').length).toBe(0);
  });

  test('should display scm subform when scm type select has a value', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      await wrapper.find('AnsibleSelect[id="scm_type"]').invoke('onChange')(
        null,
        'git'
      );
    });
    wrapper.update();
    expect(wrapper.find('FormGroup[label="Source Control URL"]').length).toBe(
      1
    );
    expect(
      wrapper.find('FormGroup[label="Source Control Branch/Tag/Commit"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Source Control Refspec"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Source Control Credential"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="Options"]').length).toBe(1);
  });

  test('inputs should update form value on change', async () => {
    const project = { ...mockData };
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          project={project}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 1,
        name: 'organization',
      });
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 10,
        name: 'credential',
      });
    });
    wrapper.update();
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 1,
      name: 'organization',
    });
    expect(wrapper.find('CredentialLookup').prop('value')).toEqual({
      id: 10,
      name: 'credential',
    });
  });

  test('should display insights credential lookup when source control type is "insights"', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      await wrapper.find('AnsibleSelect[id="scm_type"]').invoke('onChange')(
        null,
        'insights'
      );
    });
    wrapper.update();
    expect(wrapper.find('FormGroup[label="Insights Credential"]').length).toBe(
      1
    );
    await act(async () => {
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 123,
        name: 'credential',
      });
    });
    wrapper.update();
    expect(wrapper.find('CredentialLookup').prop('value')).toEqual({
      id: 123,
      name: 'credential',
    });
  });

  test('manual subform should display expected fields', async () => {
    const config = {
      project_local_paths: ['foobar', 'qux'],
      project_base_dir: 'dir/foo/bar',
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          project={{ scm_type: '', local_path: '/_foo__bar' }}
        />,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const playbookDirectorySelect = wrapper.find(
      'FormGroup[label="Playbook Directory"] FormSelect'
    );
    await act(async () => {
      playbookDirectorySelect
        .props()
        .onChange('foobar', { target: { name: 'foobar' } });
    });
    expect(wrapper.find('FormGroup[label="Project Base Path"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Playbook Directory"]').length).toBe(
      1
    );
  });

  test('manual subform should display warning message when playbook directory is empty', async () => {
    const config = {
      project_local_paths: [],
      project_base_dir: 'dir/foo/bar',
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          project={{ scm_type: '', local_path: '' }}
        />,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ManualSubForm Alert').length).toBe(1);
  });

  test('should reset source control subform values when source control type changes', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          project={{ scm_type: 'insights' }}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);

    const scmTypeSelect = wrapper.find(
      'FormGroup[label="Source Control Credential Type"] FormSelect'
    );
    await act(async () => {
      scmTypeSelect.invoke('onChange')('hg', { target: { name: 'Mercurial' } });
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('FormGroup[label="Source Control URL"] input')
        .simulate('change', {
          target: { value: 'baz', name: 'scm_url' },
        });
    });
    wrapper.update();
    expect(wrapper.find('input#project-scm-url').prop('value')).toEqual('baz');
    await act(async () => {
      scmTypeSelect
        .props()
        .onChange('insights', { target: { name: 'insights' } });
    });
    wrapper.update();
    await act(async () => {
      scmTypeSelect.props().onChange('svn', { target: { name: 'Subversion' } });
    });
    wrapper.update();
    expect(wrapper.find('input#project-scm-url').prop('value')).toEqual('');
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    const handleSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm
          project={mockData}
          handleSubmit={handleSubmit}
          handleCancel={jest.fn()}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(handleSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(handleSubmit).toBeCalled();
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    const handleCancel = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm
          project={mockData}
          handleSubmit={jest.fn()}
          handleCancel={handleCancel}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(handleCancel).toBeCalled();
  });

  test('should display ContentError on throw', async () => {
    CredentialTypesAPI.read = () => Promise.reject(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
