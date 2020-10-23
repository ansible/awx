import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import UserRolesListItem from './UserRolesListItem';

describe('<UserRolesListItem/>', () => {
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
  test('should mount properly', () => {
    wrapper = mountWithContexts(
      <UserRolesListItem
        role={role}
        detailUrl="/templates/job_template/15/details"
      />
    );
    expect(wrapper.length).toBe(1);
  });

  test('should render proper list item data', () => {
    wrapper = mountWithContexts(
      <UserRolesListItem
        role={role}
        detailUrl="/templates/job_template/15/details"
      />
    );
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
  test('should render deletable chip', () => {
    wrapper = mountWithContexts(
      <UserRolesListItem
        role={role}
        detailUrl="/templates/job_template/15/details"
      />
    );
    expect(wrapper.find('Chip').prop('isReadOnly')).toBe(false);
  });
  test('should render read only chip', () => {
    role.summary_fields.user_capabilities.unattach = false;
    wrapper = mountWithContexts(
      <UserRolesListItem
        role={role}
        detailUrl="/templates/job_template/15/details"
      />
    );
    expect(wrapper.find('Chip').prop('isReadOnly')).toBe(true);
  });
});
