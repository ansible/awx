import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import { GroupsAPI } from '@api';

import InventoryGroupForm from '../InventoryGroupForm/InventoryGroupForm';

function InventoryGroupEdit({ history, inventoryGroup, inventory, match }) {
  const [error, setError] = useState(null);

  const handleSubmit = async values => {
    try {
      await GroupsAPI.update(match.params.groupId, values);
    } catch (err) {
      setError(err);
    } finally {
      history.push(`/inventories/inventory/${inventory.id}/groups`);
    }
  };
  const handleCancel = () => {
    history.push(`/inventories/inventory/${inventory.id}/groups`);
  };
  return (
    <InventoryGroupForm
      error={error}
      group={inventoryGroup}
      handleCancel={handleCancel}
      handleSubmit={handleSubmit}
    />
  );
}
export default withI18n()(withRouter(InventoryGroupEdit));
export { InventoryGroupEdit as _InventoryGroupEdit };
