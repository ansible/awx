import React from 'react';
import { ProjectsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import ProjectsList, { _ProjectsList } from './ProjectList';

jest.mock('@api');

const mockProjects = [
  {
    id: 1,
    name: 'Project 1',
    url: '/api/v2/projects/1',
    type: 'project',
    scm_type: 'git',
    scm_revision: 'hfadsh89sa9gsaisdf0jogos0fgd9sgdf89adsf98',
    summary_fields: {
      last_job: {
        id: 9000,
        status: 'successful',
      },
      user_capabilities: {
        delete: true,
        update: true,
      },
    },
  },
  {
    id: 2,
    name: 'Project 2',
    url: '/api/v2/projects/2',
    type: 'project',
    scm_type: 'svn',
    scm_revision: '7788f7erga0jijodfgsjisiodf98sdga9hg9a98gaf',
    summary_fields: {
      last_job: {
        id: 9002,
        status: 'successful',
      },
      user_capabilities: {
        delete: true,
        update: true,
      },
    },
  },
  {
    id: 3,
    name: 'Project 3',
    url: '/api/v2/projects/3',
    type: 'project',
    scm_type: 'insights',
    scm_revision: '4893adfi749493afjksjoaiosdgjoaisdjadfisjaso',
    summary_fields: {
      last_job: {
        id: 9003,
        status: 'successful',
      },
      user_capabilities: {
        delete: false,
        update: false,
      },
    },
  },
];

describe('<ProjectsList />', () => {
  beforeEach(() => {
    ProjectsAPI.read.mockResolvedValue({
      data: {
        count: mockProjects.length,
        results: mockProjects,
      },
    });

    ProjectsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <ProjectsList
        match={{ path: '/projects', url: '/projects' }}
        location={{ search: '', pathname: '/projects' }}
      />
    );
  });

  test('Projects are retrieved from the api and the components finishes loading', async done => {
    const loadProjects = jest.spyOn(_ProjectsList.prototype, 'loadProjects');
    const wrapper = mountWithContexts(<ProjectsList />);
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === true
    );
    expect(loadProjects).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === false
    );
    done();
  });

  test('handleSelect is called when a project list item is selected', async done => {
    const handleSelect = jest.spyOn(_ProjectsList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<ProjectsList />);
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === false
    );
    await wrapper
      .find('input#select-project-1')
      .closest('DataListCheck')
      .props()
      .onChange();
    expect(handleSelect).toBeCalled();
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('selected').length === 1
    );
    done();
  });

  test('handleSelectAll is called when select all checkbox is clicked', async done => {
    const handleSelectAll = jest.spyOn(
      _ProjectsList.prototype,
      'handleSelectAll'
    );
    const wrapper = mountWithContexts(<ProjectsList />);
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === false
    );
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('selected').length === 3
    );
    done();
  });

  test('delete button is disabled if user does not have delete capabilities on a selected project', async done => {
    const wrapper = mountWithContexts(<ProjectsList />);
    wrapper.find('ProjectsList').setState({
      projects: mockProjects,
      itemCount: 3,
      isInitialized: true,
      selected: mockProjects.slice(0, 1),
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === false
    );
    wrapper.find('ProjectsList').setState({
      selected: mockProjects,
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === true
    );
    done();
  });

  test('api is called to delete projects for each selected project.', () => {
    ProjectsAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<ProjectsList />);
    wrapper.find('ProjectsList').setState({
      projects: mockProjects,
      itemCount: 2,
      isInitialized: true,
      isModalOpen: true,
      selected: mockProjects.slice(0, 2),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(ProjectsAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('error is shown when project not successfully deleted from api', async done => {
    ProjectsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/projects/1',
          },
          data: 'An error occurred',
        },
      })
    );
    const wrapper = mountWithContexts(<ProjectsList />);
    wrapper.find('ProjectsList').setState({
      projects: mockProjects,
      itemCount: 1,
      isInitialized: true,
      isModalOpen: true,
      selected: mockProjects.slice(0, 1),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    done();
  });

  test('Add button shown for users without ability to POST', async done => {
    const wrapper = mountWithContexts(<ProjectsList />);
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    done();
  });

  test('Add button hidden for users without ability to POST', async done => {
    ProjectsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    const wrapper = mountWithContexts(<ProjectsList />);
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'ProjectsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    done();
  });
});
