export default function surveyReducer(state, action) {
  switch (action.type) {
    case 'THING':
      return state;
    default:
      throw new Error(`Unrecognized action type: ${action.type}`);
  }
}

// move up/down -> Update
// delete -> Update
// delete all -> destroySurvey
// toggle -> Update survey_enabled
// select
// select all
