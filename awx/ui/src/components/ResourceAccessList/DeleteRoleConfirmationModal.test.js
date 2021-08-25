import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import DeleteRoleConfirmationModal from './DeleteRoleConfirmationModal';

const role = {
  id: 3,
  name: 'Member',
  resource_name: 'Org',
  resource_type: 'organization',
  team_id: 5,
  team_name: 'The Team',
};

describe('<DeleteRoleConfirmationModal />', () => {
  test('should render Team confirmation modal', () => {
    const wrapper = mountWithContexts(
      <DeleteRoleConfirmationModal
        role={role}
        username="jane"
        onCancel={() => {}}
        onConfirm={() => {}}
      />
    );
    wrapper.update();
    expect(wrapper.find('ModalBoxBody').text()).toBe(
      'Are you sure you want to remove Member access from The Team?  Doing so affects all members of the team.If you only want to remove access for this particular user, please remove them from the team.'
    );
    expect(wrapper.find('Title').text()).toBe('Remove Team Access');
  });

  test('should render the User confirmation delete modal', () => {
    delete role.team_id;
    const wrapper = mountWithContexts(
      <DeleteRoleConfirmationModal
        role={role}
        username="jane"
        onCancel={() => {}}
        onConfirm={() => {}}
      />
    );
    wrapper.update();
    expect(wrapper.find('Title').text()).toBe('Remove User Access');
    expect(wrapper.find('ModalBoxBody').text()).toBe(
      'Are you sure you want to remove Member access from jane?'
    );
  });
});
