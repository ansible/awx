import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import ProjectDetail from './ProjectDetail';

describe('<ProjectDetail />', () => {
  const mockProject = {
    id: 1,
    type: 'project',
    url: '/api/v2/projects/1',
    summary_fields: {
      organization: {
        id: 10,
        name: 'Foo',
      },
      credential: {
        id: 1000,
        name: 'qux',
        kind: 'scm',
      },
      last_job: {
        id: 9000,
        status: 'successful',
      },
      created_by: {
        id: 1,
        username: 'admin',
      },
      modified_by: {
        id: 1,
        username: 'admin',
      },
      user_capabilities: {
        edit: true,
        delete: true,
        start: true,
        schedule: true,
        copy: true,
      },
    },
    created: '2019-10-10T01:15:06.780472Z',
    modified: '2019-10-10T01:15:06.780490Z',
    name: 'Project 1',
    description: 'lorem ipsum',
    scm_type: 'git',
    scm_url: 'https://mock.com/bar',
    scm_branch: 'baz',
    scm_refspec: 'refs/remotes/*',
    scm_clean: true,
    scm_delete_on_update: true,
    credential: 100,
    status: 'successful',
    organization: 10,
    scm_update_on_launch: true,
    scm_update_cache_timeout: 5,
    allow_override: true,
    custom_virtualenv: '/custom-venv',
  };

  test('initially renders succesfully', () => {
    mountWithContexts(<ProjectDetail project={mockProject} />);
  });

  test('should render Details', () => {
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />, {
      context: {
        linguiPublisher: {
          i18n: {
            _: key => {
              if (key.values) {
                Object.entries(key.values).forEach(([k, v]) => {
                  key.id = key.id.replace(new RegExp(`\\{${k}\\}`), v);
                });
              }
              return key.id;
            },
          },
        },
      },
    });
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Name', mockProject.name);
    assertDetail('Description', mockProject.description);
    assertDetail('Organization', mockProject.summary_fields.organization.name);
    assertDetail('SCM Type', mockProject.scm_type);
    assertDetail('SCM URL', mockProject.scm_url);
    assertDetail('SCM Branch', mockProject.scm_branch);
    assertDetail('SCM Refspec', mockProject.scm_refspec);
    assertDetail(
      'SCM Credential',
      `Scm: ${mockProject.summary_fields.credential.name}`
    );
    assertDetail(
      'Cache Timeout',
      `${mockProject.scm_update_cache_timeout} Seconds`
    );
    assertDetail('Ansible Environment', mockProject.custom_virtualenv);
    assertDetail(
      'Created',
      `10/10/2019, 1:15:06 AM by ${mockProject.summary_fields.created_by.username}`
    );
    assertDetail(
      'Last Modified',
      `10/10/2019, 1:15:06 AM by ${mockProject.summary_fields.modified_by.username}`
    );
    expect(
      wrapper
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Clean</li>,
          <li>Delete on Update</li>,
          <li>Update Revision on Launch</li>,
          <li>Allow Branch Override</li>,
        ])
    ).toEqual(true);
  });

  test('should hide options label when all project options return false', () => {
    const mockOptions = {
      scm_clean: false,
      scm_delete_on_update: false,
      scm_update_on_launch: false,
      allow_override: false,
      created: '',
      modified: '',
    };
    const wrapper = mountWithContexts(
      <ProjectDetail project={{ ...mockProject, ...mockOptions }} />
    );
    expect(wrapper.find('Detail[label="Options"]').length).toBe(0);
  });

  test('should render with missing summary fields', async done => {
    const wrapper = mountWithContexts(
      <ProjectDetail project={{ ...mockProject, summary_fields: {} }} />
    );
    await waitForElement(
      wrapper,
      'Detail[label="Name"]',
      el => el.length === 1
    );
    done();
  });

  test('should show edit button for users with edit permission', async done => {
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />);
    const editButton = await waitForElement(
      wrapper,
      'ProjectDetail Button[aria-label="edit"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe(`/projects/${mockProject.id}/edit`);
    done();
  });

  test('should hide edit button for users without edit permission', async done => {
    const wrapper = mountWithContexts(
      <ProjectDetail
        project={{
          ...mockProject,
          summary_fields: {
            user_capabilities: {
              edit: false,
            },
          },
        }}
      />
    );
    await waitForElement(wrapper, 'ProjectDetail');
    expect(wrapper.find('ProjectDetail Button[aria-label="edit"]').length).toBe(
      0
    );
    done();
  });

  test('edit button should navigate to project edit', () => {
    const history = createMemoryHistory();
    const wrapper = mountWithContexts(<ProjectDetail project={mockProject} />, {
      context: { router: { history } },
    });
    expect(wrapper.find('Button[aria-label="edit"]').length).toBe(1);
    wrapper
      .find('Button[aria-label="edit"] Link')
      .simulate('click', { button: 0 });
    expect(history.location.pathname).toEqual('/projects/1/edit');
  });
});
