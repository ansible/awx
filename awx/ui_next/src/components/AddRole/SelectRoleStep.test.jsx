import React from 'react';
import { shallow } from 'enzyme';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import SelectRoleStep from './SelectRoleStep';

describe('<SelectRoleStep />', () => {
  let wrapper;
  const roles = {
    project_admin_role: {
      id: 1,
      name: 'Project Admin',
      description: 'Can manage all projects of the organization',
    },
    execute_role: {
      id: 2,
      name: 'Execute',
      description: 'May run any executable resources in the organization',
    },
  };
  const selectedRoles = [
    {
      id: 1,
      name: 'Project Admin',
      description: 'Can manage all projects of the organization',
    },
  ];
  const selectedResourceRows = [
    {
      id: 1,
      name: 'foo',
    },
  ];
  test('initially renders without crashing', () => {
    wrapper = shallow(
      <SelectRoleStep
        roles={roles}
        selectedResourceRows={selectedResourceRows}
        selectedRoleRows={selectedRoles}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
  test('clicking role fires onRolesClick callback', () => {
    const onRolesClick = jest.fn();
    wrapper = mountWithContexts(
      <SelectRoleStep
        onRolesClick={onRolesClick}
        roles={roles}
        selectedResourceRows={selectedResourceRows}
        selectedRoleRows={selectedRoles}
      />
    );
    const CheckboxCards = wrapper.find('CheckboxCard');
    expect(CheckboxCards.length).toBe(2);
    CheckboxCards.first().prop('onSelect')();
    expect(onRolesClick).toBeCalledWith({
      id: 1,
      name: 'Project Admin',
      description: 'Can manage all projects of the organization',
    });
    wrapper.unmount();
  });
});
