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
  const [instanceGroups, setInstanceGroups] = useState(null);
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
    try {
      if (values.instance_groups) {
        const { added, removed } = getAddedAndRemoved(
          instanceGroups,
          values.instance_groups
        );
        const update = InventoriesAPI.update(inventory.id, values);
        const associatePromises = added.map(async ig =>
          InventoriesAPI.associateInstanceGroup(inventory.id, ig.id)
        );
        const disAssociatePromises = removed.map(async ig =>
          InventoriesAPI.disassociateInstanceGroup(inventory.id, ig.id)
        );
        await Promise.all([
          update,
          ...associatePromises,
          ...disAssociatePromises,
        ]);
      } else {
        await InventoriesAPI.update(inventory.id, values);
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
          'padding-right': '10px',
          'padding-top': '10px',
          'padding-bottom': '0',
        }}
        className="at-u-textRight"
      >
        <Tooltip content={i18n._(t`Close`)} position="top">
          <CardCloseButton onClick={handleCancel} />
        </Tooltip>
      </CardHeader>
      <CardBody>
        <InventoryForm
          handleCancel={handleCancel}
          handleSubmit={handleSubmit}
          inventory={inventory}
          instanceGroups={instanceGroups}
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
