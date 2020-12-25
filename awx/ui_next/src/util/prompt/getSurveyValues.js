export default function getSurveyValues(values) {
  const surveyValues = {};
  Object.keys(values).forEach(key => {
    if (key.startsWith('survey_') && values[key] !== []) {
      if (Array.isArray(values[key]) && values[key].length === 0) {
        return;
      }
      surveyValues[key.substr(7)] = values[key];
    }
  });
  return surveyValues;
}
