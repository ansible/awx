import React from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Link } from 'react-router-dom';
import {
  Button as _Button,
  Chip as _Chip,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItemCells,
  DataListItemRow,
  DataListItem,
  Stack,
  StackItem,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';
import { CaretDownIcon, CaretUpIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const DataListAction = styled(_DataListAction)`
  margin-left: 0;
  margin-right: 20px;
  padding-top: 15px;
  padding-bottom: 15px;
`;
const Button = styled(_Button)`
  padding-top: 0;
  padding-bottom: 0;
  padding-left: 0;
`;
const Required = styled.span`
  color: red;
  margin-left: 5px;
`;
const Chip = styled(_Chip)`
  margin-right: 5px;
`;

const Label = styled.b`
  margin-right: 20px;
`;

function SurveyListItem({
  canAddAndEditSurvey,
  question,
  i18n,
  isLast,
  isFirst,
  isChecked,
  onSelect,
  onMoveUp,
  onMoveDown,
}) {
  return (
    <DataListItem
      aria-labelledby={i18n._(t`Survey questions`)}
      id={`survey-list-item-${question.variable}`}
    >
      <DataListItemRow css="padding-left:16px">
        <DataListAction
          id="sortQuestions"
          aria-labelledby={i18n._(t`Sort question order`)}
          aria-label={i18n._(t`Sort question order`)}
        >
          <Stack>
            <StackItem>
              <Button
                variant="plain"
                aria-label={i18n._(t`move up`)}
                isDisabled={isFirst || !canAddAndEditSurvey}
                onClick={() => onMoveUp(question)}
              >
                <CaretUpIcon />
              </Button>
            </StackItem>
            <StackItem>
              <Button
                variant="plain"
                aria-label={i18n._(t`move down`)}
                isDisabled={isLast || !canAddAndEditSurvey}
                onClick={() => onMoveDown(question)}
              >
                <CaretDownIcon />
              </Button>
            </StackItem>
          </Stack>
        </DataListAction>
        <DataListCheck
          isDisabled={!canAddAndEditSurvey}
          checked={isChecked}
          onChange={onSelect}
          aria-labelledby="survey check"
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <>
                <Link to={`survey/edit/${question.variable}`}>
                  {question.question_name}
                </Link>
                {question.required && (
                  <Required
                    aria-label={i18n._(t`Required`)}
                    className="pf-c-form__label-required"
                    aria-hidden="true"
                  >
                    *
                  </Required>
                )}
              </>
            </DataListCell>,

            <DataListCell key="type">
              <Label>{i18n._(t`Type:`)}</Label>
              {question.type}
            </DataListCell>,
            <DataListCell key="default">
              <Label>{i18n._(t`Default:`)}</Label>
              {[question.type].includes('password') && (
                <span>{i18n._(t`encrypted`).toUpperCase()}</span>
              )}
              {[question.type].includes('multiselect') &&
                question.default.length > 0 &&
                question.default.split('\n').map(chip => (
                  <Chip key={chip} isReadOnly>
                    {chip}
                  </Chip>
                ))}
              {![question.type].includes('password') &&
                ![question.type].includes('multiselect') && (
                  <span>{question.default}</span>
                )}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(SurveyListItem);
