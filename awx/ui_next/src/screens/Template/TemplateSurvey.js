import React, { useState, useEffect, useCallback } from 'react';
import { Switch, Route, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from 'api';
import ContentError from 'components/ContentError';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { SurveyList, SurveyQuestionAdd, SurveyQuestionEdit } from './Survey';

function TemplateSurvey({ template, canEdit }) {
  const [surveyEnabled, setSurveyEnabled] = useState(template.survey_enabled);

  const { templateType, id: templateId } = useParams();

  const {
    result: survey,
    request: fetchSurvey,
    isLoading,
    error: loadingError,
    setValue: setSurvey,
  } = useRequest(
    useCallback(async () => {
      const { data } =
        templateType === 'workflow_job_template'
          ? await WorkflowJobTemplatesAPI.readSurvey(templateId)
          : await JobTemplatesAPI.readSurvey(templateId);
      return data;
    }, [templateId, templateType])
  );

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  const {
    request: updateSurvey,
    error: updateError,
    isLoading: updateLoading,
  } = useRequest(
    useCallback(
      async (updatedSurvey) => {
        if (templateType === 'workflow_job_template') {
          await WorkflowJobTemplatesAPI.updateSurvey(templateId, updatedSurvey);
        } else {
          await JobTemplatesAPI.updateSurvey(templateId, updatedSurvey);
        }
        setSurvey(updatedSurvey);
      },
      [templateId, setSurvey, templateType]
    )
  );
  const updateSurveySpec = (spec) => {
    updateSurvey({
      name: survey?.name || '',
      description: survey?.description || '',
      spec,
    });
  };

  const { request: deleteSurvey, error: deleteError } = useRequest(
    useCallback(async () => {
      if (templateType === 'workflow_job_template') {
        await WorkflowJobTemplatesAPI.destroySurvey(templateId);
      } else {
        await JobTemplatesAPI.destroySurvey(templateId);
      }
      setSurvey(null);
    }, [templateId, setSurvey, templateType])
  );

  const { request: toggleSurvey, error: toggleError } = useRequest(
    useCallback(async () => {
      if (templateType === 'workflow_job_template') {
        await WorkflowJobTemplatesAPI.update(templateId, {
          survey_enabled: !surveyEnabled,
        });
      } else {
        await JobTemplatesAPI.update(templateId, {
          survey_enabled: !surveyEnabled,
        });
      }
      setSurveyEnabled(!surveyEnabled);
    }, [templateId, templateType, surveyEnabled])
  );

  const { error, dismissError } = useDismissableError(
    updateError || deleteError || toggleError
  );

  if (loadingError) {
    return <ContentError error={loadingError} />;
  }
  return (
    <>
      <Switch>
        {canEdit && (
          <Route path="/templates/:templateType/:id/survey/add">
            <SurveyQuestionAdd
              survey={survey}
              updateSurvey={updateSurveySpec}
            />
          </Route>
        )}
        {canEdit && (
          <Route path="/templates/:templateType/:id/survey/edit">
            <SurveyQuestionEdit
              survey={survey}
              updateSurvey={updateSurveySpec}
            />
          </Route>
        )}
        <Route path="/templates/:templateType/:id/survey" exact>
          <SurveyList
            isLoading={isLoading || updateLoading}
            survey={survey}
            surveyEnabled={surveyEnabled}
            toggleSurvey={toggleSurvey}
            updateSurvey={updateSurveySpec}
            deleteSurvey={deleteSurvey}
            canEdit={canEdit}
          />
        </Route>
      </Switch>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to update survey.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default TemplateSurvey;
