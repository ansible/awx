import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

import { CardBody, CardActionsRow } from '@components/Card';
import { DetailList, Detail } from '@components/DetailList';
import { formatDateString } from '@util/dates';

function TeamDetail({ team, i18n }) {
  const { name, description, created, modified, summary_fields } = team;
  const { id } = useParams();

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
        {summary_fields.user_capabilities.edit && (
          <Button component={Link} to={`/teams/${id}/edit`}>
            {i18n._(t`Edit`)}
          </Button>
        )}
      </CardActionsRow>
    </CardBody>
  );
}

export default withI18n()(TeamDetail);
