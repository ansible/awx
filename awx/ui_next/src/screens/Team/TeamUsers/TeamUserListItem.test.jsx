import React from 'react';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import TeamUserListItem from './TeamUserListItem';

describe('<TeamUserListItem />', () => {
  const user = {
    id: 1,
    name: 'Team 1',
    summary_fields: {
      direct_access: [
        {
          role: {
            id: 40,
            name: 'Member',
            description: 'User is a member of the team',
            resource_name: ' Team 1 Org 0',
            resource_type: 'team',
            related: {
              team: '/api/v2/teams/1/',
            },
            user_capabilities: {
              unattach: true,
            },
          },
          descendant_roles: ['member_role', 'read_role'],
        },
      ],
      indirect_access: [
        {
          role: {
            id: 2,
            name: 'Admin',
            description: 'Can manage all aspects of the organization',
            resource_name: ' Organization 0',
            resource_type: 'organization',
            related: {
              organization: '/api/v2/organizations/1/',
            },
            user_capabilities: {
              unattach: true,
            },
          },
          descendant_roles: ['admin_role', 'member_role', 'read_role'],
        },
      ],
      user_capabilities: {
        edit: true,
      },
    },
    username: 'Casey',
    firstname: 'The',
    lastname: 'Cat',
    email: '',
  };
  test('initially renders succesfully', () => {
    mountWithContexts(
      <TeamUserListItem
        user={user}
        detailUrl="/users/1/details"
        disassociateRole={() => {}}
      />
    );
  });
  test('initially render prop items', () => {
    const wrapper = mountWithContexts(
      <TeamUserListItem
        user={user}
        detailUrl="/users/1/details"
        disassociateRole={() => {}}
      />
    );
    expect(wrapper.find('DataListCell[aria-label="username"]').length).toBe(1);
    expect(wrapper.find('DataListCell[aria-label="first name"]').length).toBe(
      1
    );
    expect(wrapper.find('DataListCell[aria-label="last name"]').length).toBe(1);
    expect(wrapper.find('DataListCell[aria-label="roles"]').length).toBe(1);
    expect(
      wrapper.find('DataListCell[aria-label="indirect role"]').length
    ).toBe(1);
  });
});
