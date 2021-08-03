import React, { useState } from 'react';

import { t } from '@lingui/macro';
import { useRouteMatch } from 'react-router-dom';
import {
  Button,
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { TableComposable, Thead, Tr, Th, Tbody } from '@patternfly/react-table';
import { CubesIcon } from '@patternfly/react-icons';
import ContentLoading from 'components/ContentLoading';
import AlertModal from 'components/AlertModal';
import { ToolbarAddButton } from 'components/PaginatedTable';

import useSelected from 'hooks/useSelected';
import SurveyListItem from './SurveyListItem';
import SurveyToolbar from './SurveyToolbar';
import SurveyReorderModal from './SurveyReorderModal';

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
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);

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
      <>
        <TableComposable ouiaId="survey-list">
          <Thead>
            <Tr>
              <Th />
              <Th datalabel={t`Name`}>{t`Name`}</Th>
              <Th datalabel={t`Type`}>{t`Type`}</Th>
              <Th datalabel={t`Default`}>{t`Default`}</Th>
              <Th datalabel={t`Actions`}>{t`Actions`}</Th>
            </Tr>
          </Thead>
          <Tbody>
            {questions?.map((question, index) => (
              <SurveyListItem
                key={question.variable}
                isLast={index === questions.length - 1}
                isFirst={index === 0}
                question={question}
                isChecked={selected.some(
                  (q) => q.variable === question.variable
                )}
                onSelect={() => handleSelect(question)}
                canEdit={canEdit}
                rowIndex={index}
              />
            ))}
          </Tbody>
        </TableComposable>
        {isDeleteModalOpen && deleteModal}
        {isOrderModalOpen && (
          <SurveyReorderModal
            isOrderModalOpen={isOrderModalOpen}
            onCloseOrderModal={() => setIsOrderModalOpen(false)}
            questions={questions}
            onSave={(newOrder) => {
              updateSurvey(newOrder);
              setIsOrderModalOpen(false);
            }}
          />
        )}
      </>
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
        onOpenOrderModal={
          questions.length > 1 &&
          (() => {
            setIsOrderModalOpen(true);
          })
        }
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
