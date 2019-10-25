import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody as PFCardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';

import { DetailList, Detail } from '@components/DetailList';
import { formatDateString } from '@util/dates';

const CardBody = styled(PFCardBody)`
  padding-top: 20px;
`;

class TeamDetail extends Component {
  render() {
    const {
      team: { name, description, created, modified, summary_fields },
      match,
      i18n,
    } = this.props;

    return (
      <CardBody>
        <DetailList>
          <Detail label={i18n._(t`Name`)} value={name} />
          <Detail label={i18n._(t`Description`)} value={description} />
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link to={`/organizations/${summary_fields.organization.id}`}>
                {summary_fields.organization.name}
              </Link>
            }
          />
          <Detail
            label={i18n._(t`Created`)}
            value={formatDateString(created)}
          />
          <Detail
            label={i18n._(t`Last Modified`)}
            value={formatDateString(modified)}
          />
        </DetailList>
        {summary_fields.user_capabilities.edit && (
          <div css="margin-top: 10px; text-align: right;">
            <Button component={Link} to={`/teams/${match.params.id}/edit`}>
              {i18n._(t`Edit`)}
            </Button>
          </div>
        )}
      </CardBody>
    );
  }
}

export default withI18n()(withRouter(TeamDetail));
