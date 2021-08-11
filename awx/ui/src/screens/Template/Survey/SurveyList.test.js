import React from 'react';
import { act } from 'react-dom/test-utils';
import { JobTemplatesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyList from './SurveyList';
import mockJobTemplateData from '../shared/data.job_template.json';

jest.mock('../../../api/models/JobTemplates');

const surveyData = {
  name: 'Survey',
  description: 'description for survey',
  spec: [
    { question_name: 'Foo', type: 'text', default: 'Bar', variable: 'foo' },
    { question_name: 'Bizz', type: 'text', default: 'bazz', variable: 'bizz' },
  ],
};

describe('<SurveyList />', () => {
  test('expect component to mount successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<SurveyList survey={surveyData} />);
    });
    expect(wrapper.length).toBe(1);
  });

  test('should toggle survey', async () => {
    const toggleSurvey = jest.fn();
    JobTemplatesAPI.update.mockResolvedValue();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList
          survey={surveyData}
          surveyEnabled
          toggleSurvey={toggleSurvey}
        />
      );
    });

    expect(wrapper.find('Switch').length).toBe(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    await act(async () => {
      wrapper.find('Switch').invoke('onChange')(true);
    });

    wrapper.update();

    expect(toggleSurvey).toHaveBeenCalled();
  });

  test('should select all and delete', async () => {
    const deleteSurvey = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList survey={surveyData} deleteSurvey={deleteSurvey} canEdit />
      );
    });
    wrapper.update();

    expect(
      wrapper.find('Button[ouiaId="survey-delete-button"]').prop('isDisabled')
    ).toBe(true);
    expect(wrapper.find('Button[ouiaId="edit-order"]')).toHaveLength(1);
    expect(
      wrapper.find('Checkbox[aria-label="Select all"]').prop('isChecked')
    ).toBe(false);
    act(() => {
      wrapper.find('Checkbox[aria-label="Select all"]').invoke('onChange')(
        { target: { checked: true } },
        true
      );
    });
    wrapper.update();

    expect(
      wrapper.find('Checkbox[aria-label="Select all"]').prop('isChecked')
    ).toBe(true);
    expect(
      wrapper.find('Button[ouiaId="survey-delete-button"]').prop('isDisabled')
    ).toBe(false);
    act(() => {
      wrapper.find('Button[ouiaId="survey-delete-button"]').invoke('onClick')();
    });

    wrapper.update();

    await act(() =>
      wrapper.find('Button[aria-label="confirm delete"]').invoke('onClick')()
    );
    expect(deleteSurvey).toHaveBeenCalled();
  });

  test('should render Edit Order button ', async () => {
    let wrapper;

    await act(async () => {
      wrapper = mountWithContexts(<SurveyList survey={surveyData} canEdit />);
    });

    expect(wrapper.find('Button[ouiaId="edit-order"]').length).toBe(1);
  });

  test('Edit Order button should render Modal', async () => {
    let wrapper;

    await act(async () => {
      wrapper = mountWithContexts(<SurveyList survey={surveyData} canEdit />);
    });
    act(() => wrapper.find('Button[ouiaId="edit-order"]').prop('onClick')());
    wrapper.update();

    expect(wrapper.find('SurveyReorderModal').length).toBe(1);
  });

  test('Modal close button should close modal', async () => {
    let wrapper;

    await act(async () => {
      wrapper = mountWithContexts(<SurveyList survey={surveyData} canEdit />);
    });
    act(() => wrapper.find('Button[ouiaId="edit-order"]').prop('onClick')());
    wrapper.update();

    expect(wrapper.find('SurveyReorderModal').length).toBe(1);

    act(() => wrapper.find('Modal').prop('onClose')());

    wrapper.update();

    expect(wrapper.find('SurveyPreviewModal').length).toBe(0);
  });

  test('user without edit/delete permission cannot delete', async () => {
    const deleteSurvey = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList survey={surveyData} deleteSurvey={deleteSurvey} />
      );
    });

    expect(wrapper.find('Toolbar').find('Checkbox').prop('isDisabled')).toBe(
      true
    );
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(true);
    expect(wrapper.find('ToolbarAddButton').prop('isDisabled')).toBe(true);
    expect(wrapper.find('Button[variant="secondary"]').prop('isDisabled')).toBe(
      true
    );
  });
});

describe('Survey with no questions', () => {
  test('Survey with no questions renders empty state', async () => {
    JobTemplatesAPI.readSurvey.mockResolvedValue({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList template={mockJobTemplateData} />
      );
    });
    expect(wrapper.find('EmptyState').length).toBe(1);
    expect(wrapper.find('SurveyListItem').length).toBe(0);
  });
});
