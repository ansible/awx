import React from 'react';
import { shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';

import { formatDateString } from '../../util/dates';
import { ActionsTd, ActionItem } from '../../components/PaginatedTable';

import ActivityStreamDetailButton from './ActivityStreamDetailButton';
import ActivityStreamDescription from './ActivityStreamDescription';

function ActivityStreamListItem({ streamItem, i18n }) {
  ActivityStreamListItem.propTypes = {
    streamItem: shape({}).isRequired,
  };

  const buildUser = item => {
    let link;
    if (item?.summary_fields?.actor?.id) {
      link = (
        <Link to={`/users/${item.summary_fields.actor.id}/details`}>
          {item.summary_fields.actor.username}
        </Link>
      );
    } else if (item?.summary_fields?.actor) {
      link = i18n._(t`${item.summary_fields.actor.username} (deleted)`);
    } else {
      link = i18n._(t`system`);
    }
    return link;
  };

  const labelId = `check-action-${streamItem.id}`;
  const user = buildUser(streamItem);
  const description = <ActivityStreamDescription activity={streamItem} />;

  return (
    <Tr id={streamItem.id} aria-labelledby={labelId}>
      <Td />
      <Td dataLabel={i18n._(t`Time`)}>
        {streamItem.timestamp ? formatDateString(streamItem.timestamp) : ''}
      </Td>
      <Td dataLabel={i18n._(t`Initiated By`)}>{user}</Td>
      <Td id={labelId} dataLabel={i18n._(t`Event`)}>
        {description}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem visible tooltip={i18n._(t`View event details`)}>
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
export default withI18n()(ActivityStreamListItem);
