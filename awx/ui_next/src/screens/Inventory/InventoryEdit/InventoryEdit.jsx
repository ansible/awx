import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import { CardHeader, CardBody, Tooltip } from '@patternfly/react-core';
import { object } from 'prop-types';

import CardCloseButton from '@components/CardCloseButton';
import { InventoriesAPI, CredentialTypesAPI } from '@api';
import ContentLoading from '@components/ContentLoading';
import ContentError from '@components/ContentError';
import InventoryForm from '../shared/InventoryForm';
import { getAddedAndRemoved } from '../../../util/lists';

function InventoryEdit({ history, i18n, inventory }) {
  const [error, setError] = useState(null);
  const [associatedInstanceGroups, setInstanceGroups] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [credentialTypeId, setCredentialTypeId] = useState(null);

  useEffect(() => {
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
        setInstanceGroups(loadedInstanceGroups);
        setCredentialTypeId(loadedCredentialTypeId[0].id);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [inventory.id, isLoading, inventory, credentialTypeId]);

  const handleCancel = () => {
    history.push('/inventories');
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
        insights_credential: insights_credential.id,
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
    } catch (err) {
      setError(err);
    } finally {
      const url = history.location.pathname.search('smart')
        ? `/inventories/smart_inventory/${inventory.id}/details`
        : `/inventories/inventory/${inventory.id}/details`;
      history.push(`${url}`);
    }
  };
  if (isLoading) {
    return <ContentLoading />;
  }
  if (error) {
    return <ContentError />;
  }
  return (
    <>
      <CardHeader
        style={{
          paddingRight: '10px',
          paddingTop: '10px',
          paddingBottom: '0',
          textAlign: 'right',
        }}
      >
        <Tooltip content={i18n._(t`Close`)} position="top">
          <CardCloseButton onClick={handleCancel} />
        </Tooltip>
      </CardHeader>
      <CardBody>
        <InventoryForm
          onCancel={handleCancel}
          onSubmit={handleSubmit}
          inventory={inventory}
          instanceGroups={associatedInstanceGroups}
          credentialTypeId={credentialTypeId}
        />
      </CardBody>
    </>
  );
}

InventoryEdit.proptype = {
  inventory: object.isRequired,
};

export { InventoryEdit as _InventoryEdit };
export default withI18n()(withRouter(InventoryEdit));
