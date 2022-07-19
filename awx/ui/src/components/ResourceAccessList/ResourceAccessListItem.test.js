import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import ResourceAccessListItem from './ResourceAccessListItem';

const accessRecord = {
  id: 2,
  username: 'jane',
  url: '/bar',
  first_name: 'jane',
  last_name: 'brown',
  summary_fields: {
    direct_access: [
      {
        role: {
          id: 3,
          name: 'Member',
          resource_name: 'Org',
          resource_type: 'organization',
          team_id: 5,
          team_name: 'The Team',
          user_capabilities: { unattach: true },
        },
      },
    ],
    indirect_access: [],
  },
};

describe('<ResourceAccessListItem />', () => {
  test('initially renders successfully', async () => {
    let wrapper;

    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ResourceAccessListItem
              accessRecord={accessRecord}
              onRoleDelete={() => {}}
            />
          </tbody>
        </table>
      );
    });

    waitForElement(wrapper, 'ResourceAccessListItem', (el) => el.length > 0);

    expect(wrapper.find('Td[dataLabel="First name"]').text()).toBe('jane');
    expect(wrapper.find('Td[dataLabel="Last name"]').text()).toBe('brown');

    const user_roles_detail = wrapper.find(`Detail[label="User Roles"]`).at(0);
    expect(user_roles_detail.prop('isEmpty')).toEqual(true);
  });

  test('should not load team roles', async () => {
    let wrapper;

    await act(async () => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <ResourceAccessListItem
              accessRecord={{
                ...accessRecord,
                summary_fields: {
                  direct_access: [
                    {
                      role: {
                        id: 3,
                        name: 'Member',
                        user_capabilities: { unattach: true },
                      },
                    },
                  ],
                  indirect_access: [],
                },
              }}
              onRoleDelete={() => {}}
            />
          </tbody>
        </table>
      );
    });
    const team_roles_detail = wrapper.find(`Detail[label="Team Roles"]`).at(0);
    expect(team_roles_detail.prop('isEmpty')).toEqual(true);
  });
});
