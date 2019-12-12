import React, { useEffect, useState } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody as PFCardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';

import { OrganizationsAPI } from '@api';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip } from '@components/Chip';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { formatDateString } from '@util/dates';

const CardBody = styled(PFCardBody)`
  padding-top: 20px;
`;

function OrganizationDetail({ i18n, match, organization }) {
  const {
    params: { id },
  } = match;
  const {
    name,
    description,
    custom_virtualenv,
    max_hosts,
    created,
    modified,
    summary_fields,
  } = organization;
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [instanceGroups, setInstanceGroups] = useState([]);

  useEffect(() => {
    (async () => {
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { results = [] },
        } = await OrganizationsAPI.readInstanceGroups(id);
        setInstanceGroups(results);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [id]);

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Name`)}
          value={name}
          dataCy="organization-detail-name"
        />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail label={i18n._(t`Max Hosts`)} value={`${max_hosts}`} />
        <Detail
          label={i18n._(t`Ansible Environment`)}
          value={custom_virtualenv}
        />
        <Detail label={i18n._(t`Created`)} value={formatDateString(created)} />
        <Detail
          label={i18n._(t`Last Modified`)}
          value={formatDateString(modified)}
        />
        {instanceGroups && instanceGroups.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Instance Groups`)}
            value={
              <ChipGroup numChips={5}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>
                    {ig.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
      </DetailList>
      {summary_fields.user_capabilities.edit && (
        <div css="margin-top: 10px; text-align: right;">
          <Button component={Link} to={`/organizations/${id}/edit`}>
            {i18n._(t`Edit`)}
          </Button>
        </div>
      )}
    </CardBody>
  );
}

export default withI18n()(withRouter(OrganizationDetail));
