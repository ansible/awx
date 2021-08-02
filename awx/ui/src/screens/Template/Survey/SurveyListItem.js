import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button as _Button,
  Chip,
  Stack,
  StackItem,
  Tooltip,
} from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import {
  CaretDownIcon,
  CaretUpIcon,
  PencilAltIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import ChipGroup from 'components/ChipGroup';
import { ActionItem, ActionsTd } from 'components/PaginatedTable';

const StackButton = styled(_Button)`
  padding-top: 0;
  padding-bottom: 0;
  padding-left: 20px;
`;

const Required = styled.span`
  color: var(--pf-global--danger-color--100);
  margin-left: var(--pf-global--spacer--xs);
`;

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
  rowIndex,
}) {
  return (
    <Tr>
      <Td
        select={{
          rowIndex,
          isSelected: isChecked,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <Td id={`survey-list-item-${question.variable}`} dataLabel={t`Name`}>
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
      </Td>
      <Td dataLabel={t`Type`}>{question.type}</Td>
      <Td dataLabel={t`Default`}>
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
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem visible={canEdit}>
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
        </ActionItem>
        <ActionItem visible={canEdit}>
          <>
            <Stack>
              <StackItem>
                <StackButton
                  ouiaId={`${question.variable}-move-up-button`}
                  variant="plain"
                  aria-label={t`move up`}
                  isDisabled={isFirst || !canEdit}
                  onClick={() => onMoveUp(question)}
                >
                  <CaretUpIcon />
                </StackButton>
              </StackItem>
              <StackItem>
                <StackButton
                  ouiaId={`${question.variable}-move-down-button`}
                  variant="plain"
                  aria-label={t`move down`}
                  isDisabled={isLast || !canEdit}
                  onClick={() => onMoveDown(question)}
                >
                  <CaretDownIcon />
                </StackButton>
              </StackItem>
            </Stack>
          </>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}
export default SurveyListItem;
