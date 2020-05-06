import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { useParams, useHistory } from 'react-router-dom';
import { GroupsAPI } from '../../../api';

import InventoryGroupForm from '../shared/InventoryGroupForm';

function InventoryGroupEdit({ inventoryGroup }) {
  const [error, setError] = useState(null);
  const { id, groupId } = useParams();
  const history = useHistory();

  const handleSubmit = async values => {
    try {
      await GroupsAPI.update(groupId, values);
      history.push(`/inventories/inventory/${id}/groups/${groupId}`);
    } catch (err) {
      setError(err);
    }
  };

  const handleCancel = () => {
    history.push(`/inventories/inventory/${id}/groups/${groupId}`);
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
export default withI18n()(InventoryGroupEdit);
export { InventoryGroupEdit as _InventoryGroupEdit };
