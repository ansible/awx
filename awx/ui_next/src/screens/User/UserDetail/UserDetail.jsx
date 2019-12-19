import React, { Component } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

import { CardBody } from '@components/Card';
import { DetailList, Detail } from '@components/DetailList';
import { formatDateString } from '@util/dates';

class UserDetail extends Component {
  render() {
    const {
      user: {
        id,
        username,
        email,
        first_name,
        last_name,
        last_login,
        created,
        is_superuser,
        is_system_auditor,
        summary_fields,
      },
      i18n,
    } = this.props;

    let user_type;
    if (is_superuser) {
      user_type = i18n._(t`System Administrator`);
    } else if (is_system_auditor) {
      user_type = i18n._(t`System Auditor`);
    } else {
      user_type = i18n._(t`Normal User`);
    }

    return (
      <CardBody>
        <DetailList>
          <Detail
            label={i18n._(t`Username`)}
            value={username}
            dataCy="user-detail-username"
          />
          <Detail label={i18n._(t`Email`)} value={email} />
          <Detail label={i18n._(t`First Name`)} value={`${first_name}`} />
          <Detail label={i18n._(t`Last Name`)} value={`${last_name}`} />
          <Detail label={i18n._(t`User Type`)} value={`${user_type}`} />
          {last_login && (
            <Detail
              label={i18n._(t`Last Login`)}
              value={formatDateString(last_login)}
            />
          )}
          <Detail
            label={i18n._(t`Created`)}
            value={formatDateString(created)}
          />
        </DetailList>
        {summary_fields.user_capabilities.edit && (
          <div css="margin-top: 10px; text-align: right;">
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/users/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          </div>
        )}
      </CardBody>
    );
  }
}

export default withI18n()(withRouter(UserDetail));
