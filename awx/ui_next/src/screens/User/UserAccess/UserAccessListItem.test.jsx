import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import UserAccessListItem from './UserAccessListItem';

describe('<UserAccessListItem/>', () => {
  let wrapper;
  const role = {
    id: 1,
    name: 'Admin',
    type: 'role',
    url: '/api/v2/roles/257/',
    summary_fields: {
      resource_name: 'template delete project',
      resource_id: 15,
      resource_type: 'job_template',
      resource_type_display_name: 'Job Template',
      user_capabilities: { unattach: true },
    },
  };

  beforeEach(() => {
    wrapper = mountWithContexts(
      <UserAccessListItem
        role={role}
        detailUrl="/templates/job_template/15/details"
      />
    );
  });

  test('should mount properly', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should render proper list item data', () => {
    expect(
      wrapper.find('PFDataListCell[aria-label="resource name"]').text()
    ).toBe('template delete project');
    expect(
      wrapper.find('PFDataListCell[aria-label="resource type"]').text()
    ).toContain('Job Template');
    expect(
      wrapper.find('PFDataListCell[aria-label="resource role"]').text()
    ).toContain('Admin');
  });
});
