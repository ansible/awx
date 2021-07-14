import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import TeamRoleListItem from './TeamRoleListItem';

describe('<TeamRoleListItem/>', () => {
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
      <table>
        <tbody>
          <TeamRoleListItem
            role={role}
            detailUrl="/templates/job_template/15/details"
          />
        </tbody>
      </table>
    );

    expect(wrapper.length).toBe(1);
  });

  test('should render proper list item data', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <TeamRoleListItem
            role={role}
            detailUrl="/templates/job_template/15/details"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Td[dataLabel="Resource Name"]').text()).toBe(
      'template delete project'
    );
    expect(wrapper.find('Td[dataLabel="Type"]').text()).toContain(
      'Job Template'
    );
    expect(wrapper.find('Td[dataLabel="Role"]').text()).toContain('Admin');
  });

  test('should render deletable chip', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <TeamRoleListItem
            role={role}
            detailUrl="/templates/job_template/15/details"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Chip').prop('isReadOnly')).toBe(false);
  });
  test('should render read only chip', () => {
    role.summary_fields.user_capabilities.unattach = false;
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <TeamRoleListItem
            role={role}
            detailUrl="/templates/job_template/15/details"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Chip').prop('isReadOnly')).toBe(true);
  });
});
