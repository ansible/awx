import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import OrganizationAccessItem from './OrganizationAccessItem';

const accessRecord = {
  id: 2,
  username: 'jane',
  url: '/bar',
  first_name: 'jane',
  last_name: 'brown',
  summary_fields: {
    direct_access: [{
      role: {
        id: 3,
        name: 'Member',
        resource_name: 'Org',
        resource_type: 'organization',
        team_id: 5,
        team_name: 'The Team',
        user_capabilities: { unattach: true },
      }
    }],
    indirect_access: [],
  }
};

describe('<OrganizationAccessItem />', () => {
  test('initially renders succesfully', () => {
    const wrapper = mountWithContexts(
      <OrganizationAccessItem
        accessRecord={accessRecord}
        onRoleDelete={() => {}}
      />
    );
    expect(wrapper.find('OrganizationAccessItem')).toMatchSnapshot();
  });
});
