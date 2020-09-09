import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import DataListCell from '../../../components/DataListCell';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px;
`;

function ManagementJobListItem({ i18n, isSuperUser, id, name, description }) {
  const detailsUrl = `/management_jobs/${id}/details`;
  const editUrl = `/management_jobs/${id}/edit`;
  const labelId = `mgmt-job-action-${id}`;

  return (
    <DataListItem key={id} id={id} aria-labelledby={labelId}>
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell
              key="name"
              aria-label={i18n._(t`management job name`)}
            >
              <Link to={detailsUrl}>
                <b>{name}</b>
              </Link>
            </DataListCell>,
            <DataListCell
              key="description"
              aria-label={i18n._(t`management job description`)}
            >
              <strong>{i18n._(t`Description:`)}</strong> {description}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {isSuperUser ? (
            <Tooltip content={i18n._(t`Edit management job`)} position="top">
              <Button
                aria-label={i18n._(t`Edit management job`)}
                variant="plain"
                component={Link}
                to={editUrl}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          ) : null}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(ManagementJobListItem);
