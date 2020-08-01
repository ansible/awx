import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useRouteMatch } from 'react-router-dom';
import {
  DataList,
  Button as _Button,
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import ContentLoading from '../../../components/ContentLoading';
import AlertModal from '../../../components/AlertModal';
import { ToolbarAddButton } from '../../../components/PaginatedDataList';

import SurveyListItem from './SurveyListItem';
import SurveyToolbar from './SurveyToolbar';
import SurveyPreviewModal from './SurveyPreviewModal';

const Button = styled(_Button)`
  margin: 20px;
`;

function SurveyList({
  isLoading,
  survey,
  surveyEnabled,
  toggleSurvey,
  updateSurvey,
  deleteSurvey,
  canEdit,
  i18n,
}) {
  const match = useRouteMatch();

  const questions = survey?.spec || [];
  const [selected, setSelected] = useState([]);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const isAllSelected =
    selected.length === questions?.length && selected.length > 0;

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...questions] : []);
  };

  const handleSelect = item => {
    if (selected.some(q => q.variable === item.variable)) {
      setSelected(selected.filter(q => q.variable !== item.variable));
    } else {
      setSelected(selected.concat(item));
    }
  };

  const handleDelete = async () => {
    if (isAllSelected) {
      await deleteSurvey();
    } else {
      await updateSurvey(questions.filter(q => !selected.includes(q)));
    }
    setIsDeleteModalOpen(false);
    setSelected([]);
  };

  const moveUp = question => {
    const index = questions.indexOf(question);
    if (index < 1) {
      return;
    }
    const beginning = questions.slice(0, index - 1);
    const swapWith = questions[index - 1];
    const end = questions.slice(index + 1);
    updateSurvey([...beginning, question, swapWith, ...end]);
  };
  const moveDown = question => {
    const index = questions.indexOf(question);
    if (index === -1 || index > questions.length - 1) {
      return;
    }
    const beginning = questions.slice(0, index);
    const swapWith = questions[index + 1];
    const end = questions.slice(index + 2);
    updateSurvey([...beginning, swapWith, question, ...end]);
  };

  let content;
  if (isLoading) {
    content = <ContentLoading />;
  } else {
    content = (
      <DataList aria-label={i18n._(t`Survey List`)}>
        {questions?.map((question, index) => (
          <SurveyListItem
            key={question.variable}
            isLast={index === questions.length - 1}
            isFirst={index === 0}
            question={question}
            isChecked={selected.some(q => q.variable === question.variable)}
            onSelect={() => handleSelect(question)}
            onMoveUp={moveUp}
            onMoveDown={moveDown}
            canEdit={canEdit}
          />
        ))}
        {isPreviewModalOpen && (
          <SurveyPreviewModal
            isPreviewModalOpen={isPreviewModalOpen}
            onToggleModalOpen={() => setIsPreviewModalOpen(false)}
            questions={questions}
          />
        )}

        <Button
          onClick={() => setIsPreviewModalOpen(true)}
          variant="primary"
          aria-label={i18n._(t`Preview`)}
        >
          {i18n._(t`Preview`)}
        </Button>
      </DataList>
    );
  }
  if (isDeleteModalOpen) {
    return (
      <AlertModal
        variant="danger"
        title={
          isAllSelected ? i18n._(t`Delete Survey`) : i18n._(t`Delete Questions`)
        }
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false);
          setSelected([]);
        }}
        actions={[
          <Button
            key="delete"
            variant="danger"
            aria-label={i18n._(t`confirm delete`)}
            onClick={handleDelete}
          >
            {i18n._(t`Delete`)}
          </Button>,
          <Button
            key="cancel"
            variant="secondary"
            aria-label={i18n._(t`cancel delete`)}
            onClick={() => {
              setIsDeleteModalOpen(false);
              setSelected([]);
            }}
          >
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        <div>{i18n._(t`This action will delete the following:`)}</div>
        {selected.map(question => (
          <span key={question.variable}>
            <strong>{question.question_name}</strong>
            <br />
          </span>
        ))}
      </AlertModal>
    );
  }
  if (!questions || questions?.length <= 0) {
    return (
      <EmptyState variant="full">
        <EmptyStateIcon icon={CubesIcon} />
        <Title size="lg" headingLevel="h3">
          {i18n._(t`No survey questions found.`)}
        </Title>
        <EmptyStateBody>
          {i18n._(t`Please add survey questions.`)}
        </EmptyStateBody>
        <ToolbarAddButton isDisabled={!canEdit} linkTo={`${match.url}/add`} />
      </EmptyState>
    );
  }
  return (
    <>
      <SurveyToolbar
        isAllSelected={isAllSelected}
        onSelectAll={handleSelectAll}
        surveyEnabled={surveyEnabled}
        onToggleSurvey={toggleSurvey}
        isDeleteDisabled={selected?.length === 0}
        canEdit={canEdit}
        onToggleDeleteModal={() => setIsDeleteModalOpen(true)}
      />
      {content}
      {isDeleteModalOpen && (
        <AlertModal
          variant="danger"
          title={
            isAllSelected
              ? i18n._(t`Delete Survey`)
              : i18n._(t`Delete Questions`)
          }
          isOpen={isDeleteModalOpen}
          onClose={() => {
            setIsDeleteModalOpen(false);
          }}
          actions={[
            <Button
              key="delete"
              variant="danger"
              aria-label={i18n._(t`confirm delete`)}
              onClick={handleDelete}
            >
              {i18n._(t`Delete`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`cancel delete`)}
              onClick={() => {
                setIsDeleteModalOpen(false);
              }}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          <div>{i18n._(t`This action will delete the following:`)}</div>
          <ul>
            {selected.map(question => (
              <li key={question.variable}>
                <strong>{question.question_name}</strong>
              </li>
            ))}
          </ul>
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(SurveyList);
