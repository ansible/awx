import React from 'react';
import { act } from 'react-dom/test-utils';
import { ProjectsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ProjectList from './ProjectList';

jest.mock('../../../api');

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
  {
    id: 4,
    name: 'Project 4',
    url: '/api/v2/projects/4',
    type: 'project',
    scm_type: 'archive',
    scm_revision: 'odsd9ajf8aagjisooajfij34ikdj3fs994s4daiaos7',
    summary_fields: {
      last_job: {
        id: 9004,
        status: 'successful',
      },
      user_capabilities: {
        delete: false,
        update: false,
      },
    },
  },
];

describe('<ProjectList />', () => {
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
        related_search_fields: [],
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should load and render projects', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    expect(wrapper.find('ProjectListItem')).toHaveLength(4);
  });

  test('should select project when checked', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('ProjectListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(
      wrapper
        .find('ProjectListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should select all', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();

    const items = wrapper.find('ProjectListItem');
    expect(items).toHaveLength(4);
    items.forEach(item => {
      expect(item.prop('isSelected')).toEqual(true);
    });

    expect(
      wrapper
        .find('ProjectListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should disable delete button', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('ProjectListItem')
        .at(2)
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(wrapper.find('ToolbarDeleteButton button').prop('disabled')).toEqual(
      true
    );
  });

  test('should call delete api', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('ProjectListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('ProjectListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(ProjectsAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('should show deletion error', async () => {
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
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();
    expect(ProjectsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('ProjectListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();

    const modal = wrapper.find('Modal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });

  test('Add button shown for users without ability to POST', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('Add button hidden for users without ability to POST', async () => {
    ProjectsAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
          },
        },
      });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ProjectList />);
    });
    wrapper.update();

    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
