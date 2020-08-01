import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { useHistory, useParams } from 'react-router-dom';
import { Card } from '@patternfly/react-core';
import { GroupsAPI } from '../../../api';

import InventoryGroupForm from '../shared/InventoryGroupForm';

function InventoryGroupsAdd() {
  const [error, setError] = useState(null);
  const { id } = useParams();
  const history = useHistory();

  const handleSubmit = async values => {
    values.inventory = id;
    try {
      const { data } = await GroupsAPI.create(values);
      history.push(`/inventories/inventory/${id}/groups/${data.id}`);
    } catch (err) {
      setError(err);
    }
  };

  const handleCancel = () => {
    history.push(`/inventories/inventory/${id}/groups`);
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
export default withI18n()(InventoryGroupsAdd);
export { InventoryGroupsAdd as _InventoryGroupsAdd };
