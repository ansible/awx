import React, { useState, useCallback, useEffect } from 'react';

import { t } from '@lingui/macro';
import { useHistory, useParams, Link } from 'react-router-dom';
import { Card, PageSection } from '@patternfly/react-core';
import useRequest from 'hooks/useRequest';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { CardBody } from 'components/Card';
import { InstancesAPI } from 'api';
import InstanceForm from '../Shared/InstanceForm';

function InstanceEdit({ setBreadcrumb }) {
  const history = useHistory();
  const { id } = useParams();
  const [formError, setFormError] = useState();

  const detailsUrl = `/instances/${id}/details`;

  const handleSubmit = async (values) => {
    try {
      await InstancesAPI.update(id, values);
      history.push(detailsUrl);
    } catch (err) {
      setFormError(err);
    }
  };

  const handleCancel = () => {
    history.push(detailsUrl);
  };

  const {
    isLoading,
    error,
    request: fetchDetail,
    result: { instance, peers },
  } = useRequest(
    useCallback(async () => {
      const [{ data: instance_detail }, { data: peers_detail }] =
        await Promise.all([
          InstancesAPI.readDetail(id),
          InstancesAPI.readPeers(id),
        ]);
      return {
        instance: instance_detail,
        peers: peers_detail.results,
      };
    }, [id]),
    {
      instance: {},
      peers: [],
    }
  );

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  useEffect(() => {
    if (instance) {
      setBreadcrumb(instance);
    }
  }, [instance, setBreadcrumb]);

  if (isLoading) {
    return (
      <CardBody>
        <ContentLoading />
      </CardBody>
    );
  }

  if (error) {
    return (
      <CardBody>
        <ContentError error={error}>
          {error?.response?.status === 404 && (
            <span>
              {t`Instance not found.`}{' '}
              <Link to="/instances">{t`View all Instances.`}</Link>
            </span>
          )}
        </ContentError>
      </CardBody>
    );
  }

  return (
    <PageSection>
      <Card>
        <InstanceForm
          instance={instance}
          instance_peers={peers}
          isEdit
          submitError={formError}
          handleSubmit={handleSubmit}
          handleCancel={handleCancel}
        />
      </Card>
    </PageSection>
  );
}

export default InstanceEdit;
