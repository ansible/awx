import React, { useState, useEffect, useCallback } from 'react';
import { Switch, Route, useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../api';
import ContentError from '../../components/ContentError';
import AlertModal from '../../components/AlertModal';
import ErrorDetail from '../../components/ErrorDetail';
import useRequest, { useDismissableError } from '../../util/useRequest';
import { SurveyList, SurveyQuestionAdd, SurveyQuestionEdit } from './Survey';

function TemplateSurvey({ template, canEdit, i18n }) {
  const [surveyEnabled, setSurveyEnabled] = useState(template.survey_enabled);

  const { templateType } = useParams();
  const location = useLocation();

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
          ? await WorkflowJobTemplatesAPI.readSurvey(template.id)
          : await JobTemplatesAPI.readSurvey(template.id);
      return data;
    }, [template.id, templateType])
  );

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey, location]);

  const { request: updateSurvey, error: updateError } = useRequest(
    useCallback(
      async updatedSurvey => {
        if (templateType === 'workflow_job_template') {
          await WorkflowJobTemplatesAPI.updateSurvey(
            template.id,
            updatedSurvey
          );
        } else {
          await JobTemplatesAPI.updateSurvey(template.id, updatedSurvey);
        }
        setSurvey(updatedSurvey);
      },
      [template.id, setSurvey, templateType]
    )
  );
  const updateSurveySpec = spec => {
    updateSurvey({
      name: survey.name || '',
      description: survey.description || '',
      spec,
    });
  };

  const { request: deleteSurvey, error: deleteError } = useRequest(
    useCallback(async () => {
      await JobTemplatesAPI.destroySurvey(template.id);
      setSurvey(null);
    }, [template.id, setSurvey])
  );

  const { request: toggleSurvey, error: toggleError } = useRequest(
    useCallback(async () => {
      if (templateType === 'workflow_job_template') {
        await WorkflowJobTemplatesAPI.update(template.id, {
          survey_enabled: !surveyEnabled,
        });
      } else {
        await JobTemplatesAPI.update(template.id, {
          survey_enabled: !surveyEnabled,
        });
      }
      setSurveyEnabled(!surveyEnabled);
    }, [template.id, templateType, surveyEnabled])
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
          <Route path="/templates/:templateType/:id/survey/edit/:variable">
            <SurveyQuestionEdit
              survey={survey}
              updateSurvey={updateSurveySpec}
            />
          </Route>
        )}
        <Route path="/templates/:templateType/:id/survey" exact>
          <SurveyList
            isLoading={isLoading}
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
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to update survey.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(TemplateSurvey);
