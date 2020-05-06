import React, { useState, useEffect, useRef } from 'react';
import { useHistory } from 'react-router-dom';
import { object } from 'prop-types';

import { CardBody } from '../../../components/Card';
import { InventoriesAPI, CredentialTypesAPI } from '../../../api';
import ContentLoading from '../../../components/ContentLoading';
import InventoryForm from '../shared/InventoryForm';
import { getAddedAndRemoved } from '../../../util/lists';

function InventoryEdit({ inventory }) {
  const [error, setError] = useState(null);
  const [associatedInstanceGroups, setInstanceGroups] = useState(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [credentialTypeId, setCredentialTypeId] = useState(null);
  const history = useHistory();
  const isMounted = useRef(null);

  useEffect(() => {
    isMounted.current = true;
    const loadData = async () => {
      try {
        const [
          {
            data: { results: loadedInstanceGroups },
          },
          {
            data: { results: loadedCredentialTypeId },
          },
        ] = await Promise.all([
          InventoriesAPI.readInstanceGroups(inventory.id),
          CredentialTypesAPI.read({
            kind: 'insights',
          }),
        ]);
        if (!isMounted.current) {
          return;
        }
        setInstanceGroups(loadedInstanceGroups);
        setCredentialTypeId(loadedCredentialTypeId[0].id);
      } catch (err) {
        setError(err);
      } finally {
        if (isMounted.current) {
          setContentLoading(false);
        }
      }
    };
    loadData();
    return () => {
      isMounted.current = false;
    };
  }, [inventory.id, contentLoading, inventory, credentialTypeId]);

  const handleCancel = () => {
    const url =
      inventory.kind === 'smart'
        ? `/inventories/smart_inventory/${inventory.id}/details`
        : `/inventories/inventory/${inventory.id}/details`;

    history.push(`${url}`);
  };

  const handleSubmit = async values => {
    const {
      instanceGroups,
      insights_credential,
      organization,
      ...remainingValues
    } = values;
    try {
      await InventoriesAPI.update(inventory.id, {
        insights_credential: insights_credential
          ? insights_credential.id
          : null,
        organization: organization.id,
        ...remainingValues,
      });
      if (instanceGroups) {
        const { added, removed } = getAddedAndRemoved(
          associatedInstanceGroups,
          instanceGroups
        );

        const associatePromises = added.map(async ig =>
          InventoriesAPI.associateInstanceGroup(inventory.id, ig.id)
        );
        const disassociatePromises = removed.map(async ig =>
          InventoriesAPI.disassociateInstanceGroup(inventory.id, ig.id)
        );
        await Promise.all([...associatePromises, ...disassociatePromises]);
      }
      const url =
        history.location.pathname.search('smart') > -1
          ? `/inventories/smart_inventory/${inventory.id}/details`
          : `/inventories/inventory/${inventory.id}/details`;
      history.push(`${url}`);
    } catch (err) {
      setError(err);
    }
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
        credentialTypeId={credentialTypeId}
        submitError={error}
      />
    </CardBody>
  );
}

InventoryEdit.proptype = {
  inventory: object.isRequired,
};

export { InventoryEdit as _InventoryEdit };
export default InventoryEdit;
