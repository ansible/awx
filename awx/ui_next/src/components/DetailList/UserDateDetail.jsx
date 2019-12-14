import React from 'react';
import { node, string } from 'prop-types';
import { Link } from 'react-router-dom';
import { formatDateString } from '@util/dates';
import Detail from './Detail';
import { SummaryFieldUser } from '../../types';

function UserDateDetail({ label, date, user }) {
  return (
    <Detail
      label={label}
      value={
        <span>
          {formatDateString(date)}
          {user && ' by '}
          {user && <Link to={`/users/${user.id}`}>{user.username}</Link>}
        </span>
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
