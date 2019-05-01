import React from 'react';
import { shallow } from 'enzyme';
import { mountWithContexts } from '../enzymeHelpers';
import AddResourceRole from '../../src/components/AddRole/AddResourceRole';

describe('<AddResourceRole />', () => {
  const readUsers = jest.fn().mockResolvedValue({
    data: {
      count: 2,
      results: [
        { id: 1, username: 'foo' },
        { id: 2, username: 'bar' }
      ]
    }
  });
  const readTeams = jest.fn();
  const createUserRole = jest.fn();
  const createTeamRole = jest.fn();
  const api = { readUsers, readTeams, createUserRole, createTeamRole };
  const roles = {
    admin_role: {
      description: 'Can manage all aspects of the organization',
      id: 1,
      name: 'Admin'
    },
    execute_role: {
      description: 'May run any executable resources in the organization',
      id: 2,
      name: 'Execute'
    }
  };
  test('initially renders without crashing', () => {
    shallow(
      <AddResourceRole
        api={api}
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
      />
    );
  });
  test('handleRoleCheckboxClick properly updates state', () => {
    const wrapper = shallow(
      <AddResourceRole
        api={api}
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
      />
    );
    wrapper.setState({
      selectedRoleRows: [
        {
          description: 'Can manage all aspects of the organization',
          name: 'Admin',
          id: 1
        }
      ]
    });
    wrapper.instance().handleRoleCheckboxClick({
      description: 'Can manage all aspects of the organization',
      name: 'Admin',
      id: 1
    });
    expect(wrapper.state('selectedRoleRows')).toEqual([]);
    wrapper.instance().handleRoleCheckboxClick({
      description: 'Can manage all aspects of the organization',
      name: 'Admin',
      id: 1
    });
    expect(wrapper.state('selectedRoleRows')).toEqual([{
      description: 'Can manage all aspects of the organization',
      name: 'Admin',
      id: 1
    }]);
  });
  test('handleResourceCheckboxClick properly updates state', () => {
    const wrapper = shallow(
      <AddResourceRole
        api={api}
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
      />
    );
    wrapper.setState({
      selectedResourceRows: [
        {
          id: 1,
          username: 'foobar'
        }
      ]
    });
    wrapper.instance().handleResourceCheckboxClick({
      id: 1,
      username: 'foobar'
    });
    expect(wrapper.state('selectedResourceRows')).toEqual([]);
    wrapper.instance().handleResourceCheckboxClick({
      id: 1,
      username: 'foobar'
    });
    expect(wrapper.state('selectedResourceRows')).toEqual([{
      id: 1,
      username: 'foobar'
    }]);
  });
  test('clicking user/team cards updates state', () => {
    const spy = jest.spyOn(AddResourceRole.prototype, 'handleResourceSelect');
    const wrapper = mountWithContexts(
      <AddResourceRole
        onClose={() => {}}
        onSave={() => {}}
        api={api}
        roles={roles}
      />
    ).find('AddResourceRole');
    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(2);
    selectableCardWrapper.first().simulate('click');
    expect(spy).toHaveBeenCalledWith('users');
    expect(wrapper.state('selectedResource')).toBe('users');
    selectableCardWrapper.at(1).simulate('click');
    expect(spy).toHaveBeenCalledWith('teams');
    expect(wrapper.state('selectedResource')).toBe('teams');
  });
  test('readUsers and readTeams call out to corresponding api functions', () => {
    const wrapper = shallow(
      <AddResourceRole
        api={api}
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
      />
    );
    wrapper.instance().readUsers({
      foo: 'bar'
    });
    expect(readUsers).toHaveBeenCalledWith({
      foo: 'bar',
      is_superuser: false
    });
    wrapper.instance().readTeams({
      foo: 'bar'
    });
    expect(readTeams).toHaveBeenCalledWith({
      foo: 'bar'
    });
  });

  test('handleResourceSelect clears out selected lists and sets selectedResource', () => {
    const wrapper = shallow(
      <AddResourceRole
        api={api}
        onClose={() => {}}
        onSave={() => {}}
        roles={roles}
      />
    );
    wrapper.setState({
      selectedResource: 'teams',
      selectedResourceRows: [
        {
          id: 1,
          username: 'foobar'
        }
      ],
      selectedRoleRows: [
        {
          description: 'Can manage all aspects of the organization',
          id: 1,
          name: 'Admin'
        }
      ]
    });
    wrapper.instance().handleResourceSelect('users');
    expect(wrapper.state()).toEqual({
      selectedResource: 'users',
      selectedResourceRows: [],
      selectedRoleRows: [],
      currentStepId: 1,
    });
    wrapper.instance().handleResourceSelect('teams');
    expect(wrapper.state()).toEqual({
      selectedResource: 'teams',
      selectedResourceRows: [],
      selectedRoleRows: [],
      currentStepId: 1
    });
  });

  test('handleWizardSave makes correct api calls, calls onSave when done', async () => {
    const handleSave = jest.fn();
    const wrapper = mountWithContexts(
      <AddResourceRole
        api={api}
        onClose={() => {}}
        onSave={handleSave}
        roles={roles}
      />
    ).find('AddResourceRole');
    wrapper.setState({
      selectedResource: 'users',
      selectedResourceRows: [
        {
          id: 1,
          username: 'foobar'
        }
      ],
      selectedRoleRows: [
        {
          description: 'Can manage all aspects of the organization',
          id: 1,
          name: 'Admin'
        },
        {
          description: 'May run any executable resources in the organization',
          id: 2,
          name: 'Execute'
        }
      ]
    });
    await wrapper.instance().handleWizardSave();
    expect(createUserRole).toHaveBeenCalledTimes(2);
    expect(handleSave).toHaveBeenCalled();
    wrapper.setState({
      selectedResource: 'teams',
      selectedResourceRows: [
        {
          id: 1,
          name: 'foobar'
        }
      ],
      selectedRoleRows: [
        {
          description: 'Can manage all aspects of the organization',
          id: 1,
          name: 'Admin'
        },
        {
          description: 'May run any executable resources in the organization',
          id: 2,
          name: 'Execute'
        }
      ]
    });
    await wrapper.instance().handleWizardSave();
    expect(createTeamRole).toHaveBeenCalledTimes(2);
    expect(handleSave).toHaveBeenCalled();
  });
});
