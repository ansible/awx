import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { TeamsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import TeamEdit from './TeamEdit';

jest.mock('../../../api');

describe('<TeamEdit />', () => {
  const mockData = {
    name: 'Foo',
    description: 'Bar',
    id: 1,
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
      },
    },
  };

  test('handleSubmit should call api update and then navigate to the details page', async () => {
    const history = createMemoryHistory({});

    const wrapper = mountWithContexts(<TeamEdit team={mockData} />, {
      context: { router: { history } },
    });

    const updatedTeamData = {
      name: 'new name',
      description: 'new description',
    };
    await act(async () => {
      wrapper.find('TeamForm').invoke('handleSubmit')(updatedTeamData);
    });

    expect(TeamsAPI.update).toHaveBeenCalledWith(1, updatedTeamData);
    expect(history.location.pathname).toEqual('/teams/1/details');
  });

  test('should navigate to team detail when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    const wrapper = mountWithContexts(<TeamEdit team={mockData} />, {
      context: { router: { history } },
    });

    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });

    expect(history.location.pathname).toEqual('/teams/1/details');
  });
});
