export default function getSurveyValues(values) {
  const surveyValues = {};
  Object.keys(values).forEach(key => {
    if (key.startsWith('survey_')) {
      surveyValues[key.substr(7)] = values[key];
    }
  });
  return surveyValues;
}
