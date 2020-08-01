import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import TeamAdd from './TeamAdd';
import { TeamsAPI } from '../../../api';

jest.mock('../../../api');

describe('<TeamAdd />', () => {
  test('handleSubmit should post to api', async () => {
    TeamsAPI.create.mockResolvedValueOnce({ data: {} });
    const wrapper = mountWithContexts(<TeamAdd />);
    const updatedTeamData = {
      name: 'new name',
      description: 'new description',
      organization: 1,
    };
    await act(async () => {
      wrapper.find('TeamForm').invoke('handleSubmit')(updatedTeamData);
    });
    expect(TeamsAPI.create).toHaveBeenCalledWith(updatedTeamData);
  });

  test('should navigate to teams list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    const wrapper = mountWithContexts(<TeamAdd />, {
      context: { router: { history } },
    });
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/teams');
  });

  test('successful form submission should trigger redirect', async () => {
    const history = createMemoryHistory({});
    const teamData = {
      name: 'new name',
      description: 'new description',
      organization: 1,
    };
    TeamsAPI.create.mockResolvedValueOnce({
      data: {
        id: 5,
        ...teamData,
        summary_fields: {
          organization: {
            id: 1,
            name: 'Default',
          },
        },
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<TeamAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      await wrapper.find('TeamForm').invoke('handleSubmit')(teamData);
    });
    expect(history.location.pathname).toEqual('/teams/5');
  });
});
