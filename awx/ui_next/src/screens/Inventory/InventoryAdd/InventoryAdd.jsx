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
    try {
      let response;
      if (values.instance_groups) {
        response = await InventoriesAPI.create(values);
        const associatePromises = values.instance_groups.map(async ig =>
          InventoriesAPI.associateInstanceGroup(response.data.id, ig.id)
        );
        await Promise.all([response, ...associatePromises]);
      } else {
        response = await InventoriesAPI.create(values);
      }
      const url = history.location.pathname.search('smart')
        ? `/inventories/smart_inventory/${response.data.id}/details`
        : `/inventories/inventory/${response.data.id}/details`;

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
            credentialTypeId={credentialTypeId}
          />
        </CardBody>
      </Card>
    </PageSection>
  );
}

export { InventoryAdd as _InventoryAdd };
export default withI18n()(withRouter(InventoryAdd));
