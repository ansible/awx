import React from 'react';
import { act } from 'react-dom/test-utils';
import { UsersAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import UserTeamList from './UserTeamList';

jest.mock('../../../api');

const mockAPIUserTeamList = {
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

describe('<UserTeamList />', () => {
  beforeEach(() => {
    UsersAPI.readTeams = jest.fn(() =>
      Promise.resolve({
        data: mockAPIUserTeamList.data,
      })
    );
    UsersAPI.readTeamsOptions = jest.fn(() =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
          related_search_fields: [],
        },
      })
    );
  });

  test('should load and render teams', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<UserTeamList />);
    });
    wrapper.update();

    expect(wrapper.find('UserTeamListItem')).toHaveLength(3);
  });
});
