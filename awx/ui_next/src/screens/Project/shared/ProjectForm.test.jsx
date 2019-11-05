import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import ProjectForm from './ProjectForm';
import { CredentialTypesAPI, ProjectsAPI } from '@api';

jest.mock('@api');

describe('<ProjectAdd />', () => {
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
    expect(wrapper.find('FormGroup[label="SCM Type"]').length).toBe(1);
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
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      formik.setState(
        {
          values: {
            ...mockData,
          },
        },
        () => resolve()
      );
    });
    await changeState;
    wrapper.update();
    expect(wrapper.find('FormGroup[label="SCM URL"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SCM Branch/Tag/Commit"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="SCM Refspec"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="SCM Credential"]').length).toBe(1);
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
    const form = wrapper.find('Formik');
    act(() => {
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 1,
        name: 'organization',
      });
    });
    expect(form.state('values').organization).toEqual(1);
    act(() => {
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 10,
        name: 'credential',
      });
    });
    expect(form.state('values').credential).toEqual(10);
  });

  test('should display insights credential lookup when scm type is "Insights"', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ProjectForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const formik = wrapper.find('Formik').instance();
    const changeState = new Promise(resolve => {
      formik.setState(
        {
          values: {
            ...mockData,
            scm_type: 'insights',
          },
        },
        () => resolve()
      );
    });
    await changeState;
    wrapper.update();
    expect(wrapper.find('FormGroup[label="Insights Credential"]').length).toBe(
      1
    );
    act(() => {
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 123,
        name: 'credential',
      });
    });
    expect(formik.state.values.credential).toEqual(123);
  });

  test('should reset scm subform values when scm type changes', async () => {
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
      'FormGroup[label="SCM Type"] FormSelect'
    );
    const formik = wrapper.find('Formik').instance();
    expect(formik.state.values.scm_url).toEqual('');
    await act(async () => {
      scmTypeSelect.props().onChange('hg', { target: { name: 'Mercurial' } });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('FormGroup[label="SCM URL"] input').simulate('change', {
        target: { value: 'baz', name: 'scm_url' },
      });
    });
    expect(formik.state.values.scm_url).toEqual('baz');
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
    expect(formik.state.values.scm_url).toEqual('');
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
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
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
