import React, { useState } from 'react';

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
import ContentLoading from 'components/ContentLoading';
import AlertModal from 'components/AlertModal';
import { ToolbarAddButton } from 'components/PaginatedTable';

import useSelected from 'hooks/useSelected';
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
}) {
  const match = useRouteMatch();

  const questions = survey?.spec || [];
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

  const { selected, isAllSelected, setSelected, selectAll, clearSelected } =
    useSelected(questions);

  const handleSelect = (item) => {
    if (selected.some((q) => q.variable === item.variable)) {
      setSelected(selected.filter((q) => q.variable !== item.variable));
    } else {
      setSelected(selected.concat(item));
    }
  };

  const handleDelete = async () => {
    if (isAllSelected) {
      await deleteSurvey();
    } else {
      await updateSurvey(questions.filter((q) => !selected.includes(q)));
    }
    setIsDeleteModalOpen(false);
    clearSelected();
  };

  const moveUp = (question) => {
    const index = questions.indexOf(question);
    if (index < 1) {
      return;
    }
    const beginning = questions.slice(0, index - 1);
    const swapWith = questions[index - 1];
    const end = questions.slice(index + 1);
    updateSurvey([...beginning, question, swapWith, ...end]);
  };
  const moveDown = (question) => {
    const index = questions.indexOf(question);
    if (index === -1 || index > questions.length - 1) {
      return;
    }
    const beginning = questions.slice(0, index);
    const swapWith = questions[index + 1];
    const end = questions.slice(index + 2);
    updateSurvey([...beginning, swapWith, question, ...end]);
  };
  const deleteModal = (
    <AlertModal
      variant="danger"
      title={isAllSelected ? t`Delete Survey` : t`Delete Questions`}
      isOpen={isDeleteModalOpen}
      onClose={() => {
        setIsDeleteModalOpen(false);
        clearSelected();
      }}
      actions={[
        <Button
          ouiaId="delete-confirm-button"
          key="delete"
          variant="danger"
          aria-label={t`confirm delete`}
          onClick={handleDelete}
        >
          {t`Delete`}
        </Button>,
        <Button
          ouiaId="delete-cancel-button"
          key="cancel"
          variant="link"
          aria-label={t`cancel delete`}
          onClick={() => {
            setIsDeleteModalOpen(false);
            clearSelected();
          }}
        >
          {t`Cancel`}
        </Button>,
      ]}
    >
      <div>{t`This action will delete the following:`}</div>
      {selected.map((question) => (
        <span key={question.variable}>
          <strong>{question.question_name}</strong>
          <br />
        </span>
      ))}
    </AlertModal>
  );

  let content;
  if (isLoading) {
    content = <ContentLoading />;
  } else {
    content = (
      <DataList aria-label={t`Survey List`}>
        {questions?.map((question, index) => (
          <SurveyListItem
            key={question.variable}
            isLast={index === questions.length - 1}
            isFirst={index === 0}
            question={question}
            isChecked={selected.some((q) => q.variable === question.variable)}
            onSelect={() => handleSelect(question)}
            onMoveUp={moveUp}
            onMoveDown={moveDown}
            canEdit={canEdit}
          />
        ))}
        {isDeleteModalOpen && deleteModal}
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
          aria-label={t`Preview`}
        >
          {t`Preview`}
        </Button>
      </DataList>
    );
  }

  if ((!questions || questions?.length <= 0) && !isLoading) {
    return (
      <EmptyState variant="full">
        <EmptyStateIcon icon={CubesIcon} />
        <Title size="lg" headingLevel="h3">
          {t`No survey questions found.`}
        </Title>
        <EmptyStateBody>{t`Please add survey questions.`}</EmptyStateBody>
        <ToolbarAddButton isDisabled={!canEdit} linkTo={`${match.url}/add`} />
      </EmptyState>
    );
  }
  return (
    <>
      <SurveyToolbar
        isAllSelected={isAllSelected}
        onSelectAll={selectAll}
        surveyEnabled={surveyEnabled}
        onToggleSurvey={toggleSurvey}
        isDeleteDisabled={selected?.length === 0}
        canEdit={canEdit}
        onToggleDeleteModal={() => setIsDeleteModalOpen(true)}
      />
      {content}
    </>
  );
}

export default SurveyList;
