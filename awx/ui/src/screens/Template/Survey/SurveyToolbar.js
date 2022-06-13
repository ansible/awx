import React from 'react';
import { useRouteMatch } from 'react-router-dom';
import { t } from '@lingui/macro';

import styled from 'styled-components';

import {
  Switch,
  Checkbox,
  Button,
  Toolbar as _Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
  Tooltip,
} from '@patternfly/react-core';
import { ToolbarAddButton } from 'components/PaginatedTable';

const Toolbar = styled(_Toolbar)`
  margin-left: 10px;
`;
const SwitchWrapper = styled(ToolbarItem)`
  padding-left: 4px;
`;

function SurveyToolbar({
  canEdit,
  isAllSelected,
  onSelectAll,
  surveyEnabled,
  onToggleSurvey,
  isDeleteDisabled,
  onToggleDeleteModal,
  onOpenOrderModal,
  emptyList,
}) {
  isDeleteDisabled = !canEdit || isDeleteDisabled;
  const match = useRouteMatch();
  return (
    <Toolbar id="survey-toolbar" ouiaId="survey-toolbar">
      <ToolbarContent>
        <ToolbarItem>
          <Checkbox
            isDisabled={!canEdit}
            isChecked={isAllSelected}
            onChange={(isChecked) => {
              onSelectAll(isChecked);
            }}
            aria-label={t`Select all`}
            id="select-all"
            ouiaId="select-all"
          />
        </ToolbarItem>
        <ToolbarGroup>
          <ToolbarItem>
            <ToolbarAddButton
              isDisabled={!canEdit}
              linkTo={`${match.url}/add`}
            />
          </ToolbarItem>
          {canEdit && onOpenOrderModal && (
            <ToolbarItem>
              <Tooltip
                content={t`Click to rearrange the order of the survey questions`}
              >
                <Button
                  onClick={() => {
                    onOpenOrderModal();
                  }}
                  variant="secondary"
                  ouiaId="edit-order"
                >
                  {t`Edit Order`}
                </Button>
              </Tooltip>
            </ToolbarItem>
          )}
          <ToolbarItem>
            <Tooltip
              content={
                isDeleteDisabled
                  ? t`Select a question to delete`
                  : t`Delete survey question`
              }
            >
              <div>
                <Button
                  ouiaId="survey-delete-button"
                  variant="secondary"
                  isDisabled={isDeleteDisabled}
                  onClick={() => onToggleDeleteModal(true)}
                >
                  {t`Delete`}
                </Button>
              </div>
            </Tooltip>
          </ToolbarItem>
        </ToolbarGroup>
        {!emptyList && (
          <SwitchWrapper>
            <Switch
              aria-label={t`Survey Toggle`}
              id="survey-toggle"
              label={t`Survey Enabled`}
              labelOff={t`Survey Disabled`}
              isChecked={surveyEnabled}
              isDisabled={!canEdit}
              onChange={() => onToggleSurvey(!surveyEnabled)}
            />
          </SwitchWrapper>
        )}
      </ToolbarContent>
    </Toolbar>
  );
}

export default SurveyToolbar;
