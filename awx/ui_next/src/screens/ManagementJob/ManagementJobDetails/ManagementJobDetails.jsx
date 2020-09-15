import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import { Button } from '@patternfly/react-core';

import { SystemJobTemplatesAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import {
  Detail,
  DetailList,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import { useConfig } from '../../../contexts/Config';

function ManagementJobDetails({ i18n, managementJob }) {
  const { me } = useConfig();

  const history = useHistory();
  const [isLaunchLoading, setIsLaunchLoading] = useState(false);
  const [launchError, setLaunchError] = useState(null);

  const handleLaunch = async () => {
    setIsLaunchLoading(true);
    try {
      const { data } = await SystemJobTemplatesAPI.launch(managementJob?.id);
      history.push(`/jobs/management/${data.id}/output`);
    } catch (error) {
      setLaunchError(error);
    } finally {
      setIsLaunchLoading(false);
    }
  };

  if (!managementJob) return null;

  return (
    <>
      <CardBody>
        <DetailList>
          <Detail
            label={i18n._(t`Name`)}
            dataCy="management-job-detail-name"
            value={managementJob.name}
          />
          <Detail
            label={i18n._(t`Description`)}
            dataCy="management-job-detail-description"
            value={managementJob.description}
          />
          {managementJob?.has_configurable_retention ? (
            <Detail
              label={i18n._(t`Data retention`)}
              dataCy="management-job-detail-data-retention"
              value={`${managementJob.default_days} ${i18n._(t`days`)}`}
            />
          ) : null}
          <UserDateDetail
            label={i18n._(t`Created`)}
            date={managementJob?.created}
            user={managementJob?.summary_fields?.created_by}
          />
          <UserDateDetail
            label={i18n._(t`Last Modified`)}
            date={managementJob.modified}
            user={managementJob?.summary_fields?.modified_by}
          />
        </DetailList>
        <CardActionsRow>
          {me?.is_superuser && managementJob?.has_configurable_retention ? (
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/management_jobs/${managementJob?.id}/edit`}
              isDisabled={isLaunchLoading}
            >
              {i18n._(t`Edit`)}
            </Button>
          ) : null}
          {me?.is_superuser ? (
            <Button
              aria-label={i18n._(t`Launch management job`)}
              variant="secondary"
              onClick={handleLaunch}
              isDisabled={isLaunchLoading}
            >
              {i18n._(t`Launch`)}
            </Button>
          ) : null}
        </CardActionsRow>
      </CardBody>
      <AlertModal
        isOpen={Boolean(launchError)}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={() => setLaunchError(null)}
      >
        {i18n._(t`Failed to launch job.`)}
        <ErrorDetail error={launchError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(ManagementJobDetails);
