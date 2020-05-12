import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

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
  test('initially renders succesfully', () => {
    const wrapper = mountWithContexts(
      <ResourceAccessListItem
        accessRecord={accessRecord}
        onRoleDelete={() => {}}
      />
    );
    expect(wrapper.find('ResourceAccessListItem')).toMatchSnapshot();
  });
});
