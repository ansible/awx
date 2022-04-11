import React, { useState } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { CardBody } from 'components/Card';
import SurveyQuestionForm from './SurveyQuestionForm';

export default function SurveyQuestionAdd({ survey, updateSurvey }) {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const match = useRouteMatch();

  const handleSubmit = async (question) => {
    const formData = { ...question };
    try {
      if (survey?.spec?.some((q) => q.variable === formData.variable)) {
        setFormError(
          new Error(
            `Survey already contains a question with variable named “${formData.variable}”`
          )
        );
        return;
      }
      if (
        formData.type === 'multiselect' ||
        formData.type === 'multiplechoice'
      ) {
        const choices = [];
        let defaultAnswers = '';
        formData.formattedChoices.forEach(({ choice, isDefault }, i) => {
          choices.push(choice);
          // i === formData.formattedChoices.length - 1
          //   ? choices.concat(`${choice}`)
          //   : choices.concat(`${choice}\n`);
          if (isDefault) {
            defaultAnswers =
              i === formData.formattedChoices.length - 1
                ? defaultAnswers.concat(`${choice}`)
                : defaultAnswers.concat(`${choice}\n`);
          }
        });
        formData.default = defaultAnswers.trim();
        formData.choices = choices;
      }
      delete formData.formattedChoices;
      const newSpec = survey?.spec ? survey.spec.concat(formData) : [formData];
      await updateSurvey(newSpec);
      history.push(match.url.replace('/add', ''));
    } catch (err) {
      setFormError(err);
    }
  };

  const handleCancel = () => {
    history.push(match.url.replace('/add', ''));
  };

  return (
    <CardBody>
      <SurveyQuestionForm
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
        submitError={formError}
      />
    </CardBody>
  );
}
