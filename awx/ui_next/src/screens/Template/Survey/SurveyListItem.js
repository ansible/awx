import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button as _Button,
  Chip,
  DataListAction as _DataListAction,
  DataListCell,
  DataListCheck,
  DataListItemCells,
  DataListItemRow,
  DataListItem,
  Stack,
  StackItem,
  Tooltip,
} from '@patternfly/react-core';
import {
  CaretDownIcon,
  CaretUpIcon,
  PencilAltIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import ChipGroup from 'components/ChipGroup';

const DataListAction = styled(_DataListAction)`
  && {
    margin-left: 0;
    margin-right: 20px;
    padding-top: 0;
    padding-bottom: 0;
  }
`;

const Button = styled(_Button)`
  padding-top: 0;
  padding-bottom: 0;
  padding-left: 0;
`;

const Required = styled.span`
  color: var(--pf-global--danger-color--100);
  margin-left: var(--pf-global--spacer--xs);
`;

const Label = styled.b`
  margin-right: 20px;
`;

const EditSection = styled(_DataListAction)``;

const EditButton = styled(_Button)``;

function SurveyListItem({
  canEdit,
  question,
  isLast,
  isFirst,
  isChecked,
  onSelect,
  onMoveUp,
  onMoveDown,
}) {
  return (
    <DataListItem
      aria-labelledby={t`Survey questions`}
      id={`survey-list-item-${question.variable}`}
    >
      <DataListItemRow css="padding-left:16px">
        <DataListAction
          id="sortQuestions"
          aria-labelledby={t`Sort question order`}
          aria-label={t`Sort question order`}
        >
          <Stack>
            <StackItem>
              <Button
                ouiaId={`${question.variable}-move-up-button`}
                variant="plain"
                aria-label={t`move up`}
                isDisabled={isFirst || !canEdit}
                onClick={() => onMoveUp(question)}
              >
                <CaretUpIcon />
              </Button>
            </StackItem>
            <StackItem>
              <Button
                ouiaId={`${question.variable}-move-down-button`}
                variant="plain"
                aria-label={t`move down`}
                isDisabled={isLast || !canEdit}
                onClick={() => onMoveDown(question)}
              >
                <CaretDownIcon />
              </Button>
            </StackItem>
          </Stack>
        </DataListAction>
        <DataListCheck
          isDisabled={!canEdit}
          checked={isChecked}
          onChange={onSelect}
          aria-labelledby="survey check"
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <>
                <Link
                  to={`survey/edit?question_variable=${encodeURIComponent(
                    question.variable
                  )}`}
                >
                  {question.question_name}
                </Link>
                {question.required && (
                  <Required
                    aria-label={t`Required`}
                    className="pf-c-form__label-required"
                    aria-hidden="true"
                  >
                    *
                  </Required>
                )}
              </>
            </DataListCell>,
            <DataListCell key="type">
              <Label>{t`Type`}</Label>
              {question.type}
            </DataListCell>,
            <DataListCell key="default">
              <Label>{t`Default`}</Label>
              {[question.type].includes('password') && (
                <span>{t`encrypted`.toUpperCase()}</span>
              )}
              {[question.type].includes('multiselect') &&
                question.default.length > 0 && (
                  <ChipGroup
                    numChips={5}
                    totalChips={question.default.split('\n').length}
                  >
                    {question.default.split('\n').map((chip) => (
                      <Chip key={chip} isReadOnly>
                        {chip}
                      </Chip>
                    ))}
                  </ChipGroup>
                )}
              {![question.type].includes('password') &&
                ![question.type].includes('multiselect') && (
                  <span>{question.default}</span>
                )}
            </DataListCell>,
          ]}
        />
        <EditSection aria-label={t`actions`}>
          {canEdit && (
            <EditButton variant="plain">
              <Tooltip content={t`Edit Survey`} position="top">
                <EditButton
                  ouiaId={`edit-survey-${question.variable}`}
                  aria-label={t`edit survey`}
                  variant="plain"
                  component={Link}
                  to={`survey/edit?question_variable=${encodeURIComponent(
                    question.variable
                  )}`}
                >
                  <PencilAltIcon />
                </EditButton>
              </Tooltip>
            </EditButton>
          )}
        </EditSection>
      </DataListItemRow>
    </DataListItem>
  );
}
export default SurveyListItem;
