import React, { useState, useEffect, useCallback } from 'react';
import { Switch, Route } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { JobTemplatesAPI } from '@api';
import ContentError from '@components/ContentError';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import useRequest, { useDismissableError } from '@util/useRequest';
import { SurveyList, SurveyQuestionAdd, SurveyQuestionEdit } from './Survey';

function TemplateSurvey({ template, i18n }) {
  const [surveyEnabled, setSurveyEnabled] = useState(template.survey_enabled);

  const {
    result: survey,
    request: fetchSurvey,
    isLoading,
    error: loadingError,
    setValue: setSurvey,
  } = useRequest(
    useCallback(async () => {
      const { data } = await JobTemplatesAPI.readSurvey(template.id);
      return data;
    }, [template.id])
  );
  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  const { request: updateSurvey, error: updateError } = useRequest(
    useCallback(
      async updatedSurvey => {
        await JobTemplatesAPI.updateSurvey(template.id, updatedSurvey);
        setSurvey(updatedSurvey);
      },
      [template.id, setSurvey]
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
      await JobTemplatesAPI.update(template.id, {
        survey_enabled: !surveyEnabled,
      });
      setSurveyEnabled(!surveyEnabled);
    }, [template.id, surveyEnabled])
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
        <Route path="/templates/:templateType/:id/survey/add">
          <SurveyQuestionAdd survey={survey} updateSurvey={updateSurveySpec} />
        </Route>
        <Route path="/templates/:templateType/:id/survey/edit/:variable">
          <SurveyQuestionEdit survey={survey} updateSurvey={updateSurveySpec} />
        </Route>
        <Route path="/templates/:templateType/:id/survey" exact>
          <SurveyList
            isLoading={isLoading}
            survey={survey}
            surveyEnabled={surveyEnabled}
            toggleSurvey={toggleSurvey}
            updateSurvey={updateSurveySpec}
            deleteSurvey={deleteSurvey}
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
