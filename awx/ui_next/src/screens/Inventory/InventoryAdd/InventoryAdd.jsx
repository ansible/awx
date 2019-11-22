import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  PageSection,
  Card,
  CardHeader,
  CardBody,
  Tooltip,
} from '@patternfly/react-core';

import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';

import CardCloseButton from '@components/CardCloseButton';
import { InventoriesAPI, CredentialTypesAPI } from '@api';
import InventoryForm from '../shared/InventoryForm';

function InventoryAdd({ history, i18n }) {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [credentialTypeId, setCredentialTypeId] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const {
          data: { results: loadedCredentialTypeId },
        } = await CredentialTypesAPI.read({ kind: 'insights' });
        setCredentialTypeId(loadedCredentialTypeId[0].id);
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [isLoading, credentialTypeId]);

  const handleCancel = () => {
    history.push('/inventories');
  };

  const handleSubmit = async values => {
    const {
      instanceGroups,
      organization,
      insights_credential,
      ...remainingValues
    } = values;
    try {
      const {
        data: { id: inventoryId },
      } = await InventoriesAPI.create({
        organization: organization.id,
        insights_credential: insights_credential.id,
        ...remainingValues,
      });
      if (instanceGroups) {
        const associatePromises = instanceGroups.map(async ig =>
          InventoriesAPI.associateInstanceGroup(inventoryId, ig.id)
        );
        await Promise.all(associatePromises);
      }
      const url = history.location.pathname.search('smart')
        ? `/inventories/smart_inventory/${inventoryId}/details`
        : `/inventories/inventory/${inventoryId}/details`;

      history.push(`${url}`);
    } catch (err) {
      setError(err);
    }
  };

  if (error) {
    return <ContentError />;
  }
  if (isLoading) {
    return <ContentLoading />;
  }
  return (
    <PageSection>
      <Card>
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
            credentialTypeId={credentialTypeId}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { InventoryAdd as _InventoryAdd };
export default withI18n()(withRouter(InventoryAdd));
