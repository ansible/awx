import React, { useEffect, useCallback, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import useRequest, { useDeleteItems } from '@util/useRequest';
import { Button } from '@patternfly/react-core';

import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import ErrorDetail from '@components/ErrorDetail';
import { JobTemplatesAPI } from '@api';
import ContentEmpty from '@components/ContentEmpty';
import { getQSConfig } from '@util/qs';
import AlertModal from '@components/AlertModal';
import SurveyListItem from './SurveyListItem';
import SurveyToolbar from './SurveyToolbar';

const QS_CONFIG = getQSConfig('survey', {
  page: 1,
});

function SurveyList({ template, i18n }) {
  const [selected, setSelected] = useState([]);
  const [surveyEnabled, setSurveyEnabled] = useState(template.survey_enabled);
  const [showToggleError, setShowToggleError] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const {
    result: { questions, name, description },
    error: contentError,
    isLoading,
    request: fetchSurvey,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { spec = [], description: surveyDescription, name: surveyName },
      } = await JobTemplatesAPI.readSurvey(template.id);
      return {
        questions: spec.map((s, index) => ({ ...s, id: index })),
        description: surveyDescription,
        name: surveyName,
      };
    }, [template.id]),
    { questions: [], name: '', description: '' }
  );

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  const isAllSelected =
    selected.length === questions?.length && selected.length > 0;

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteQuestions,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      if (isAllSelected) {
        return JobTemplatesAPI.destroySurvey(template.id);
      }
      const surveyQuestions = [];
      questions.forEach(q => {
        if (!selected.some(s => s.id === q.id)) {
          surveyQuestions.push(q);
        }
      });
      return JobTemplatesAPI.updateSurvey(template.id, {
        name,
        description,
        spec: surveyQuestions,
      });
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      fetchItems: fetchSurvey,
    }
  );
  const {
    isToggleLoading,
    error: toggleError,
    request: toggleSurvey,
  } = useRequest(
    useCallback(async () => {
      await JobTemplatesAPI.update(template.id, {
        survey_enabled: !surveyEnabled,
      });
      return setSurveyEnabled(!surveyEnabled);
    }, [template, surveyEnabled]),
    template.survey_enabled
  );

  useEffect(() => {
    if (toggleError) {
      setShowToggleError(true);
    }
  }, [toggleError]);

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...questions] : []);
  };

  const handleSelect = item => {
    if (selected.some(s => s.id === item.id)) {
      setSelected(selected.filter(s => s.id !== item.id));
    } else {
      setSelected(selected.concat(item));
    }
  };

  const handleDelete = async () => {
    await deleteQuestions();
    setIsDeleteModalOpen(false);
    setSelected([]);
  };
  const canEdit = template.summary_fields.user_capabilities.edit;
  const canDelete = template.summary_fields.user_capabilities.delete;

  let content;
  if (isLoading || isToggleLoading || isDeleteLoading) {
    content = <ContentLoading />;
  } else if (contentError) {
    content = <ContentError error={contentError} />;
  } else if (!questions || questions?.length <= 0) {
    content = (
      <ContentEmpty
        title={i18n._(t`No Survey Questions Found`)}
        message={i18n._(t`Please add survey questions.`)}
      />
    );
  } else {
    content = questions?.map((question, index) => (
      <SurveyListItem
        key={question.id}
        isLast={index === questions.length - 1}
        isFirst={index === 0}
        question={question}
        isChecked={selected.some(s => s.id === question.id)}
        onSelect={() => handleSelect(question)}
      />
    ));
  }
  return (
    <>
      <SurveyToolbar
        isAllSelected={isAllSelected}
        onSelectAll={handleSelectAll}
        surveyEnabled={surveyEnabled}
        onToggleSurvey={toggleSurvey}
        isDeleteDisabled={selected?.length === 0 || !canEdit || !canDelete}
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
            <span key={question.id}>
              <strong>{question.question_name}</strong>
              <br />
            </span>
          ))}
        </AlertModal>
      )}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more jobs.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
      {toggleError && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={showToggleError && !isLoading}
          onClose={() => setShowToggleError(false)}
        >
          {i18n._(t`Failed to toggle host.`)}
          <ErrorDetail error={toggleError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(SurveyList);
