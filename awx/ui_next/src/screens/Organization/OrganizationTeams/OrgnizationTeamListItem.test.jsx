import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import OrganizationTeamListItem from './OrganizationTeamListItem';

const team = {
  id: 1,
  name: 'one',
  url: '/org/team/1',
  summary_fields: { user_capabilities: { edit: true, delete: true } },
};

describe('<OrganizationTeamListItem />', () => {
  let wrapper;
  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationTeamListItem team={team} detailUrl="/teams/1" />
      );
    });
    expect(wrapper.find('OrganizationTeamListItem').length).toBe(1);
  });

  test('should render proper data', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationTeamListItem team={team} detailUrl="/teams/1" />
      );
    });
    expect(wrapper.find(`b[aria-label="team name"]`).text()).toBe('one');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
  });

  test('should not render edit button', async () => {
    team.summary_fields.user_capabilities.edit = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationTeamListItem team={team} detailUrl="/teams/1" />
      );
    });
    expect(wrapper.find('PencilAltIcon').length).toBe(0);
  });
});
