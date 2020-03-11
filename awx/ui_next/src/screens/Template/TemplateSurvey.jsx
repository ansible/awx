import React, { useState, useEffect } from 'react';
import { Switch, Route } from 'react-router-dom';
import { JobTemplatesAPI } from '@api';
import SurveyList from './shared/SurveyList';

export default function TemplateSurvey({ template }) {
  const [survey, setSurvey] = useState(null);
  const [surveyEnabled, setSurveyEnabled] = useState(template.survey_enabled);

  useEffect(() => {
    (async () => {
      const { data } = await JobTemplatesAPI.readSurvey(template.id);
      setSurvey(data);
    })();
  }, [template.id]);

  const updateSurvey = async newQuestions => {
    await JobTemplatesAPI.updateSurvey(template.id, {
      ...survey,
      spec: newQuestions,
    });
    setSurvey({
      ...survey,
      spec: newQuestions,
    });
  };

  const deleteSurvey = async () => {
    await JobTemplatesAPI.destroySurvey(template.id);
    setSurvey(null);
  };

  const toggleSurvey = async () => {
    await JobTemplatesAPI.update(template.id, {
      survey_enabled: !surveyEnabled,
    });
    setSurveyEnabled(!surveyEnabled);
  };

  // TODO
  // if (contentError) {
  // return <ContentError error={contentError} />;
  return (
    <Switch>
      <Route path="/templates/:templateType/:id/survey">
        <SurveyList
          survey={survey}
          surveyEnabled={surveyEnabled}
          toggleSurvey={toggleSurvey}
          updateSurvey={updateSurvey}
          deleteSurvey={deleteSurvey}
        />
      </Route>
    </Switch>
  );
}
