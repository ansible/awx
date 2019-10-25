import React from 'react';
import { createMemoryHistory } from 'history';
import { TeamsAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import TeamEdit from './TeamEdit';

jest.mock('@api');

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

  test('handleSubmit should call api update', () => {
    const wrapper = mountWithContexts(<TeamEdit team={mockData} />);

    const updatedTeamData = {
      name: 'new name',
      description: 'new description',
    };
    wrapper.find('TeamForm').prop('handleSubmit')(updatedTeamData);

    expect(TeamsAPI.update).toHaveBeenCalledWith(1, updatedTeamData);
  });

  test('should navigate to team detail when cancel is clicked', () => {
    const history = createMemoryHistory({});
    const wrapper = mountWithContexts(<TeamEdit team={mockData} />, {
      context: { router: { history } },
    });

    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();

    expect(history.location.pathname).toEqual('/teams/1/details');
  });
});
