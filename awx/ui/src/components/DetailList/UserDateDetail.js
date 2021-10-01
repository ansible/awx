import React from 'react';
import { node, string } from 'prop-types';
import { Trans } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { formatDateString } from 'util/dates';
import { SummaryFieldUser } from 'types';
import _Detail from './Detail';

const Detail = styled(_Detail)`
  word-break: break-word;
`;

function UserDateDetail({ label, date, user }) {
  const dateStr = formatDateString(date);
  const username = user ? user.username : '';
  return (
    <Detail
      label={label}
      dataCy="user-date-detail"
      value={
        user ? (
          <Trans>
            {dateStr} by <Link to={`/users/${user.id}`}>{username}</Link>
          </Trans>
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

export default UserDateDetail;
