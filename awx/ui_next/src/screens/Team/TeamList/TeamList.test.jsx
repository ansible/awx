import React from 'react';
import { act } from 'react-dom/test-utils';
import { TeamsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import TeamList from './TeamList';

jest.mock('../../../api');

const mockAPITeamList = {
  data: {
    count: 3,
    results: [
      {
        name: 'Team 0',
        id: 1,
        url: '/teams/1',
        summary_fields: {
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
      {
        name: 'Team 1',
        id: 2,
        url: '/teams/2',
        summary_fields: {
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
      {
        name: 'Team 2',
        id: 3,
        url: '/teams/3',
        summary_fields: {
          user_capabilities: {
            delete: true,
            edit: true,
          },
        },
      },
    ],
  },
  isModalOpen: false,
  warningTitle: 'title',
  warningMsg: 'message',
};

describe('<TeamList />', () => {
  beforeEach(() => {
    TeamsAPI.read = jest.fn(() =>
      Promise.resolve({
        data: mockAPITeamList.data,
      })
    );
    TeamsAPI.readOptions = jest.fn(() =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      })
    );
  });

  test('should load and render teams', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();

    expect(wrapper.find('TeamListItem')).toHaveLength(3);
  });

  test('should select team when checked', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('TeamListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(
      wrapper
        .find('TeamListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should select all', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();

    const items = wrapper.find('TeamListItem');
    expect(items).toHaveLength(3);
    items.forEach(item => {
      expect(item.prop('isSelected')).toEqual(true);
    });

    expect(
      wrapper
        .find('TeamListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should call delete api', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('TeamListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('TeamListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(TeamsAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('should re-fetch teams after team(s) have been deleted', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();
    expect(TeamsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('TeamListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(TeamsAPI.read).toHaveBeenCalledTimes(2);
  });

  test('should show deletion error', async () => {
    TeamsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/teams/1',
          },
          data: 'An error occurred',
        },
      })
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();
    expect(TeamsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('TeamListItem')
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
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();

    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('Add button hidden for users without ability to POST', async () => {
    TeamsAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
          },
        },
      });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamList />);
    });
    wrapper.update();

    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
