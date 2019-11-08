import React from 'react';
import { TeamsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import TeamsList, { _TeamsList } from './TeamList';

jest.mock('@api');

const mockAPITeamsList = {
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
          },
        },
      },
    ],
  },
  isModalOpen: false,
  warningTitle: 'title',
  warningMsg: 'message',
};

describe('<TeamsList />', () => {
  let wrapper;

  beforeEach(() => {
    TeamsAPI.read = () =>
      Promise.resolve({
        data: mockAPITeamsList.data,
      });
    TeamsAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
  });

  test('initially renders succesfully', () => {
    mountWithContexts(<TeamsList />);
  });

  test('Selects one team when row is checked', async () => {
    wrapper = mountWithContexts(<TeamsList />);
    await waitForElement(
      wrapper,
      'TeamsList',
      el => el.state('hasContentLoading') === false
    );
    expect(
      wrapper
        .find('input[type="checkbox"]')
        .findWhere(n => n.prop('checked') === true).length
    ).toBe(0);
    wrapper
      .find('TeamListItem')
      .at(0)
      .find('DataListCheck')
      .props()
      .onChange(true);
    wrapper.update();
    expect(
      wrapper
        .find('input[type="checkbox"]')
        .findWhere(n => n.prop('checked') === true).length
    ).toBe(1);
  });

  test('Select all checkbox selects and unselects all rows', async () => {
    wrapper = mountWithContexts(<TeamsList />);
    await waitForElement(
      wrapper,
      'TeamsList',
      el => el.state('hasContentLoading') === false
    );
    expect(
      wrapper
        .find('input[type="checkbox"]')
        .findWhere(n => n.prop('checked') === true).length
    ).toBe(0);
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    wrapper.update();
    expect(
      wrapper
        .find('input[type="checkbox"]')
        .findWhere(n => n.prop('checked') === true).length
    ).toBe(4);
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(false);
    wrapper.update();
    expect(
      wrapper
        .find('input[type="checkbox"]')
        .findWhere(n => n.prop('checked') === true).length
    ).toBe(0);
  });

  test('api is called to delete Teams for each team in selected.', () => {
    wrapper = mountWithContexts(<TeamsList />);
    const component = wrapper.find('TeamsList');
    wrapper.find('TeamsList').setState({
      teams: mockAPITeamsList.data.results,
      itemCount: 3,
      isInitialized: true,
      isModalOpen: mockAPITeamsList.isModalOpen,
      selected: mockAPITeamsList.data.results,
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(TeamsAPI.destroy).toHaveBeenCalledTimes(
      component.state('selected').length
    );
  });

  test('call loadTeams after team(s) have been deleted', () => {
    const fetchTeams = jest.spyOn(_TeamsList.prototype, 'loadTeams');
    const event = { preventDefault: () => {} };
    wrapper = mountWithContexts(<TeamsList />);
    wrapper.find('TeamsList').setState({
      teams: mockAPITeamsList.data.results,
      itemCount: 3,
      isInitialized: true,
      selected: mockAPITeamsList.data.results.slice(0, 1),
    });
    const component = wrapper.find('TeamsList');
    component.instance().handleTeamDelete(event);
    expect(fetchTeams).toBeCalled();
  });

  test('error is shown when team not successfully deleted from api', async done => {
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

    wrapper = mountWithContexts(<TeamsList />);
    wrapper.find('TeamsList').setState({
      teams: mockAPITeamsList.data.results,
      itemCount: 3,
      isInitialized: true,
      selected: mockAPITeamsList.data.results.slice(0, 1),
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
    wrapper = mountWithContexts(<TeamsList />);
    await waitForElement(
      wrapper,
      'TeamsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'TeamsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    done();
  });

  test('Add button hidden for users without ability to POST', async done => {
    TeamsAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
          },
        },
      });
    wrapper = mountWithContexts(<TeamsList />);
    await waitForElement(
      wrapper,
      'TeamsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'TeamsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    done();
  });
});
