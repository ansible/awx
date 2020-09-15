import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCell,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon, RocketIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import { SystemJobTemplatesAPI } from '../../../api';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(2, 40px);
`;

function ManagementJobListItem({
  i18n,
  onLaunchError,
  isConfigurable,
  isSuperUser,
  id,
  name,
  description,
}) {
  const detailsUrl = `/management_jobs/${id}/details`;
  const editUrl = `/management_jobs/${id}/edit`;
  const labelId = `mgmt-job-action-${id}`;

  const history = useHistory();
  const [isLaunchLoading, setIsLaunchLoading] = useState(false);

  const handleLaunch = async () => {
    setIsLaunchLoading(true);
    try {
      const { data } = await SystemJobTemplatesAPI.launch(id);
      history.push(`/jobs/management/${data.id}/output`);
    } catch (error) {
      onLaunchError(error);
    } finally {
      setIsLaunchLoading(false);
    }
  };

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
            <>
              <Tooltip
                content={i18n._(t`Launch management job`)}
                position="top"
              >
                <Button
                  aria-label={i18n._(t`Launch management job`)}
                  variant="plain"
                  onClick={handleLaunch}
                  isDisabled={isLaunchLoading}
                >
                  <RocketIcon />
                </Button>
              </Tooltip>
              {isConfigurable ? (
                <Tooltip
                  content={i18n._(t`Edit management job`)}
                  position="top"
                >
                  <Button
                    aria-label={i18n._(t`Edit management job`)}
                    variant="plain"
                    component={Link}
                    to={editUrl}
                    isDisabled={isLaunchLoading}
                  >
                    <PencilAltIcon />
                  </Button>
                </Tooltip>
              ) : null}
            </>
          ) : null}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(ManagementJobListItem);
