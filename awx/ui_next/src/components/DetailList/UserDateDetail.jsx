import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { node, string } from 'prop-types';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

import { formatDateString } from '../../util/dates';
import _Detail from './Detail';
import { SummaryFieldUser } from '../../types';

const Detail = styled(_Detail)`
  word-break: break-word;
`;

function UserDateDetail({ i18n, label, date, user, dataCy = null }) {
  const dateStr = formatDateString(date);
  const username = user ? user.username : '';
  return (
    <Detail
      label={label}
      dataCy={dataCy}
      value={
        user ? (
          <span>
            {dateStr} {i18n._(t`by`)}{' '}
            <Link to={`/users/${user.id}`}>{username}</Link>
          </span>
        ) : (
          dateStr
        )
      }
    />
  );
}
UserDateDetail.propTypes = {
  label: node.isRequired,
  date: string.isRequired,
  user: SummaryFieldUser,
};
UserDateDetail.defaultProps = {
  user: null,
};

export default withI18n()(UserDateDetail);
