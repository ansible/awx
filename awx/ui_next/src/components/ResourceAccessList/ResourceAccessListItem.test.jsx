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

    waitForElement(wrapper, 'ResourceAccessListItem', el => el.length > 0);
  });
});
