import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { object } from 'prop-types';

import { CardBody } from 'components/Card';
import { InventoriesAPI } from 'api';
import { getAddedAndRemoved } from 'util/lists';
import ContentLoading from 'components/ContentLoading';
import useIsMounted from 'hooks/useIsMounted';
import InventoryForm from '../shared/InventoryForm';

function InventoryEdit({ inventory }) {
  const [error, setError] = useState(null);
  const [associatedInstanceGroups, setInstanceGroups] = useState(null);
  const [contentLoading, setContentLoading] = useState(true);
  const history = useHistory();
  const isMounted = useIsMounted();

  useEffect(() => {
    const loadData = async () => {
      try {
        const {
          data: { results: loadedInstanceGroups },
        } = await InventoriesAPI.readInstanceGroups(inventory.id);
        if (!isMounted.current) {
          return;
        }
        setInstanceGroups(loadedInstanceGroups);
      } catch (err) {
        setError(err);
      } finally {
        if (isMounted.current) {
          setContentLoading(false);
        }
      }
    };
    loadData();
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [inventory.id, contentLoading, inventory]);

  const handleCancel = () => {
    const url =
      inventory.kind === 'smart'
        ? `/inventories/smart_inventory/${inventory.id}/details`
        : `/inventories/inventory/${inventory.id}/details`;

    history.push(`${url}`);
  };

  const handleSubmit = async (values) => {
    const { instanceGroups, organization, ...remainingValues } = values;
    try {
      await InventoriesAPI.update(inventory.id, {
        organization: organization.id,
        ...remainingValues,
      });
      await InventoriesAPI.orderInstanceGroups(
        inventory.id,
        instanceGroups,
        associatedInstanceGroups
      );
      await submitLabels(values.organization.id, values.labels);

      const url =
        history.location.pathname.search('smart') > -1
          ? `/inventories/smart_inventory/${inventory.id}/details`
          : `/inventories/inventory/${inventory.id}/details`;
      history.push(`${url}`);
    } catch (err) {
      setError(err);
    }
  };

  const submitLabels = async (orgId, labels = []) => {
    const { added, removed } = getAddedAndRemoved(
      inventory.summary_fields.labels.results,
      labels
    );

    const disassociationPromises = removed.map((label) =>
      InventoriesAPI.disassociateLabel(inventory.id, label)
    );
    const associationPromises = added.map((label) =>
      InventoriesAPI.associateLabel(inventory.id, label, orgId)
    );

    const results = await Promise.all([
      ...disassociationPromises,
      ...associationPromises,
    ]);
    return results;
  };

  if (contentLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <InventoryForm
        onCancel={handleCancel}
        onSubmit={handleSubmit}
        inventory={inventory}
        instanceGroups={associatedInstanceGroups}
        submitError={error}
      />
    </CardBody>
  );
}

InventoryEdit.propType = {
  inventory: object.isRequired,
};

export { InventoryEdit as _InventoryEdit };
export default InventoryEdit;
