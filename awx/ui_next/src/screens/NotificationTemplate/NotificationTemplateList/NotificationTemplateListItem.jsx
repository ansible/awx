import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon, BellIcon } from '@patternfly/react-icons';
import DataListCell from '../../../components/DataListCell';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px 40px;
`;

function NotificationTemplateListItem({
  template,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
}) {
  const sendTestNotification = () => {};
  const labelId = `template-name-${template.id}`;

  return (
    <DataListItem key={template.id} aria-labelledby={labelId} id={template.id}>
      <DataListItemRow>
        <DataListCheck
          id={`select-template-${template.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" id={labelId}>
              <Link to={detailUrl}>
                <b>{template.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {template.notification_type}
            </DataListCell>,
          ]}
        />
        <DataListAction aria-label="actions" aria-labelledby={labelId}>
          {template.summary_fields.user_capabilities.edit ? (
            <Tooltip
              content={i18n._(t`Edit Notification Template`)}
              position="top"
            >
              <Button
                aria-label={i18n._(t`Edit Notification Template`)}
                variant="plain"
                component={Link}
                to={`/notification_templates/${template.id}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          ) : (
            <div />
          )}
          <Tooltip content={i18n._(t`Test Notification`)} position="top">
            <Button
              aria-label={i18n._(t`Test Notification`)}
              variant="plain"
              onClick={sendTestNotification}
            >
              <BellIcon />
            </Button>
          </Tooltip>
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(NotificationTemplateListItem);
