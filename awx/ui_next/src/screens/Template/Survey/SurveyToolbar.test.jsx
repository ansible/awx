import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { act } from 'react-dom/test-utils';
import SurveyToolbar from './SurveyToolbar';

jest.mock('@api/models/JobTemplates');

describe('<SurveyToolbar />', () => {
  test('delete Button is disabled', () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyToolbar
          isDeleteDisabled
          onSelectAll={jest.fn()}
          isAllSelected
          onToggleDeleteModal={jest.fn()}
          onToggleSurvey={jest.fn()}
        />
      );
    });

    expect(wrapper.find('Button[variant="danger"]').prop('isDisabled')).toBe(
      true
    );
  });

  test('delete Button is enabled', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyToolbar
          isDeleteDisabled={false}
          onSelectAll={jest.fn()}
          isAllSelected
          onToggleDeleteModal={jest.fn()}
          onToggleSurvey={jest.fn()}
        />
      );
    });
    expect(
      wrapper.find('Checkbox[aria-label="Select all"]').prop('isChecked')
    ).toBe(true);
    expect(wrapper.find('Button[variant="danger"]').prop('isDisabled')).toBe(
      false
    );
  });

  test('switch is off', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyToolbar
          surveyEnabled={false}
          isDeleteDisabled={false}
          onSelectAll={jest.fn()}
          isAllSelected
          onToggleDelete={jest.fn()}
          onToggleSurvey={jest.fn()}
        />
      );
    });

    expect(wrapper.find('Switch').length).toBe(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
  });

  test('switch is on', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyToolbar
          surveyEnabled
          isDeleteDisabled={false}
          onSelectAll={jest.fn()}
          isAllSelected
          onToggleDelete={jest.fn()}
          onToggleSurvey={jest.fn()}
        />
      );
    });

    expect(wrapper.find('Switch').length).toBe(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
  });
});
