import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import { GroupsAPI } from '@api';
import { Card } from '@patternfly/react-core';

import InventoryGroupForm from '../shared/InventoryGroupForm';

function InventoryGroupsAdd({ history, inventory, setBreadcrumb }) {
  const [error, setError] = useState(null);

  useEffect(() => setBreadcrumb(inventory), [inventory, setBreadcrumb]);

  const handleSubmit = async values => {
    values.inventory = inventory.id;
    try {
      const { data } = await GroupsAPI.create(values);
      history.push(`/inventories/inventory/${inventory.id}/groups/${data.id}`);
    } catch (err) {
      setError(err);
    }
  };

  const handleCancel = () => {
    history.push(`/inventories/inventory/${inventory.id}/groups`);
  };

  return (
    <Card>
      <InventoryGroupForm
        error={error}
        handleCancel={handleCancel}
        handleSubmit={handleSubmit}
      />
    </Card>
  );
}
export default withI18n()(withRouter(InventoryGroupsAdd));
export { InventoryGroupsAdd as _InventoryGroupsAdd };
