import React from 'react';
import { useRouteMatch } from 'react-router-dom';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';

import {
  DataToolbar as _DataToolbar,
  DataToolbarContent,
  DataToolbarGroup,
  DataToolbarItem,
} from '@patternfly/react-core/dist/umd/experimental';
import { Switch, Checkbox, Button } from '@patternfly/react-core';
import { ToolbarAddButton } from '../../../components/PaginatedDataList';

const DataToolbar = styled(_DataToolbar)`
  margin-left: 52px;
`;

function SurveyToolbar({
  canEdit,
  isAllSelected,
  onSelectAll,
  i18n,
  surveyEnabled,
  onToggleSurvey,
  isDeleteDisabled,
  onToggleDeleteModal,
}) {
  isDeleteDisabled = !canEdit || isDeleteDisabled;
  const match = useRouteMatch();
  return (
    <DataToolbar id="survey-toolbar">
      <DataToolbarContent>
        <DataToolbarItem>
          <Checkbox
            isDisabled={!canEdit}
            isChecked={isAllSelected}
            onChange={isChecked => {
              onSelectAll(isChecked);
            }}
            aria-label={i18n._(t`Select all`)}
            id="select-all"
          />
        </DataToolbarItem>
        <DataToolbarItem>
          <Switch
            aria-label={i18n._(t`Survey Toggle`)}
            id="survey-toggle"
            label={i18n._(t`On`)}
            labelOff={i18n._(t`Off`)}
            isChecked={surveyEnabled}
            isDisabled={!canEdit}
            onChange={() => onToggleSurvey(!surveyEnabled)}
          />
        </DataToolbarItem>
        <DataToolbarGroup>
          <DataToolbarItem>
            <ToolbarAddButton
              isDisabled={!canEdit}
              linkTo={`${match.url}/add`}
            />
          </DataToolbarItem>
          <DataToolbarItem>
            <Button
              variant="danger"
              isDisabled={isDeleteDisabled}
              onClick={() => onToggleDeleteModal(true)}
            >
              {i18n._(t`Delete`)}
            </Button>
          </DataToolbarItem>
        </DataToolbarGroup>
      </DataToolbarContent>
    </DataToolbar>
  );
}

export default withI18n()(SurveyToolbar);
