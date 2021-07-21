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
      <table>
        <tbody>
          <UserRolesListItem
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
          <UserRolesListItem
            role={role}
            detailUrl="/templates/job_template/15/details"
          />
        </tbody>
      </table>
    );
    const cells = wrapper.find('Td');
    expect(cells.at(0).text()).toBe('template delete project');
    expect(cells.at(1).text()).toContain('Job Template');
    expect(cells.at(2).text()).toContain('Admin');
  });

  test('should render deletable chip', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <UserRolesListItem
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
          <UserRolesListItem
            role={role}
            detailUrl="/templates/job_template/15/details"
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Chip').prop('isReadOnly')).toBe(true);
  });

  test('should display System as name when no resource_name is present in summary_fields', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <UserRolesListItem
            role={{
              ...role,
              summary_fields: {
                user_capabilities: { unattach: false },
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Td').at(0).text()).toBe('System');
  });
});
