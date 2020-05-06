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
  test('should render initially', () => {
    const wrapper = mountWithContexts(
      <DeleteRoleConfirmationModal
        role={role}
        username="jane"
        onCancel={() => {}}
        onConfirm={() => {}}
      />
    );
    wrapper.update();
    expect(wrapper.find('DeleteRoleConfirmationModal')).toMatchSnapshot();
  });
});
