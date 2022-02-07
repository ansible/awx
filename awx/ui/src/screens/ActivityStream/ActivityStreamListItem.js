import React from 'react';
import { shape } from 'prop-types';

import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';

import { formatDateString } from 'util/dates';
import { ActionsTd, ActionItem } from 'components/PaginatedTable';

import ActivityStreamDetailButton from './ActivityStreamDetailButton';
import ActivityStreamDescription from './ActivityStreamDescription';

function ActivityStreamListItem({ streamItem }) {
  ActivityStreamListItem.propTypes = {
    streamItem: shape({}).isRequired,
  };

  const buildUser = (item) => {
    let link;
    if (item?.summary_fields?.actor?.id) {
      link = (
        <Link to={`/users/${item.summary_fields.actor.id}/details`}>
          {item.summary_fields.actor.username}
        </Link>
      );
    } else if (item?.summary_fields?.actor) {
      link = t`${item.summary_fields.actor.username} (deleted)`;
    } else {
      link = t`system`;
    }
    return link;
  };

  const labelId = `check-action-${streamItem.id}`;
  const user = buildUser(streamItem);
  const description = <ActivityStreamDescription activity={streamItem} />;

  return (
    <Tr id={streamItem.id} ouiaId={streamItem.id} aria-labelledby={labelId}>
      <Td />
      <Td dataLabel={t`Time`}>
        {streamItem.timestamp ? formatDateString(streamItem.timestamp) : ''}
      </Td>
      <Td dataLabel={t`Initiated By`}>{user}</Td>
      <Td id={labelId} dataLabel={t`Event`}>
        {description}
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem visible tooltip={t`View event details`}>
          <ActivityStreamDetailButton
            streamItem={streamItem}
            user={user}
            description={description}
          />
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}
export default ActivityStreamListItem;
