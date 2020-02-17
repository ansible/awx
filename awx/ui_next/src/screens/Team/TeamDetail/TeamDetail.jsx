import React, { useState } from 'react';
import { Link, useHistory, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

import AlertModal from '@components/AlertModal';
import { CardBody, CardActionsRow } from '@components/Card';
import ContentLoading from '@components/ContentLoading';
import DeleteButton from '@components/DeleteButton';
import { DetailList, Detail } from '@components/DetailList';
import ErrorDetail from '@components/ErrorDetail';
import { formatDateString } from '@util/dates';
import { TeamsAPI } from '@api';

function TeamDetail({ team, i18n }) {
  const { name, description, created, modified, summary_fields } = team;
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(false);
  const history = useHistory();
  const { id } = useParams();

  const handleDelete = async () => {
    setHasContentLoading(true);
    try {
      await TeamsAPI.destroy(id);
      history.push(`/teams`);
    } catch (error) {
      setDeletionError(error);
    }
    setHasContentLoading(false);
  };

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={name}
          dataCy="team-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail
          label={i18n._(t`Organization`)}
          value={
            <Link to={`/organizations/${summary_fields.organization.id}`}>
              {summary_fields.organization.name}
            </Link>
          }
        />
        <Detail label={i18n._(t`Created`)} value={formatDateString(created)} />
        <Detail
          label={i18n._(t`Last Modified`)}
          value={formatDateString(modified)}
        />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              aria-label={i18n._(t`Edit`)}
              component={Link}
              to={`/teams/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={name}
              modalTitle={i18n._(t`Delete Team`)}
              onConfirm={handleDelete}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete team.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default withI18n()(TeamDetail);
