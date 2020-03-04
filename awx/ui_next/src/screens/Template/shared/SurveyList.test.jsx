import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import SurveyList from './SurveyList';
import { JobTemplatesAPI } from '@api';
import mockJobTemplateData from './data.job_template.json';

jest.mock('@api/models/JobTemplates');

describe('<SurveyList />', () => {
  beforeEach(() => {
    JobTemplatesAPI.readSurvey.mockResolvedValue({
      data: { spec: [{ question_name: 'Foo', type: 'text', default: 'Bar' }] },
    });
  });
  test('expect component to mount successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = await mountWithContexts(
        <SurveyList template={mockJobTemplateData} />
      );
    });
    expect(wrapper.length).toBe(1);
  });
  test('expect api to be called to get survey', async () => {
    let wrapper;
    await act(async () => {
      wrapper = await mountWithContexts(
        <SurveyList template={mockJobTemplateData} />
      );
    });
    expect(JobTemplatesAPI.readSurvey).toBeCalledWith(7);
    wrapper.update();
    expect(wrapper.find('SurveyListItem').length).toBe(1);
  });
  test('error in retrieving the survey throws an error', async () => {
    JobTemplatesAPI.readSurvey.mockRejectedValue(new Error());
    let wrapper;
    await act(async () => {
      wrapper = await mountWithContexts(
        <SurveyList template={{ ...mockJobTemplateData, id: 'a' }} />
      );
    });
    wrapper.update();
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
