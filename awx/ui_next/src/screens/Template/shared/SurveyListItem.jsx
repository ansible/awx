import React from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import {
  Button as _Button,
  DataList,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItemCells,
  DataListItemRow,
  DataListItem,
  DataListCell,
  Stack,
  StackItem,
} from '@patternfly/react-core';
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
function SurveyListItem({ question, i18n, isLast, isFirst }) {
  return (
    <DataList aria-label={i18n._(t`Survey List`)}>
      <DataListItem aria-labelledby={i18n._(t`Survey questions`)}>
        <DataListItemRow>
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
                  isDisabled={isFirst}
                >
                  <CaretUpIcon />
                </Button>
              </StackItem>
              <StackItem>
                <Button
                  variant="plain"
                  aria-label={i18n._(t`move down`)}
                  isDisabled={isLast}
                >
                  <CaretDownIcon />
                </Button>
              </StackItem>
            </Stack>
          </DataListAction>
          <DataListCheck checked={false} aria-labelledby="survey check" />
          <DataListItemCells
            dataListCells={[
              <DataListCell key={question.question_name}>
                {question.question_name}
              </DataListCell>,
              <DataListCell key={question.type}>{question.type}</DataListCell>,
              <DataListCell key={question.default}>
                {question.default}
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    </DataList>
  );
}

export default withI18n()(SurveyListItem);
