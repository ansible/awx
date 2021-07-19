import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyToolbar from './SurveyToolbar';

jest.mock('../../../api/models/JobTemplates');

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

    expect(wrapper.find('Button[variant="secondary"]').prop('isDisabled')).toBe(
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
          canEdit
        />
      );
    });
    expect(
      wrapper.find('Checkbox[aria-label="Select all"]').prop('isChecked')
    ).toBe(true);
    expect(wrapper.find('Button[variant="secondary"]').prop('isDisabled')).toBe(
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
  test('all action buttons in toolbar are disabled', () => {
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
          canEdit={false}
        />
      );
    });
    expect(
      wrapper
        .find('Toolbar')
        .find('Checkbox')
        .prop('isDisabled')
    ).toBe(true);
    expect(wrapper.find('Switch').prop('isDisabled')).toBe(true);
    expect(wrapper.find('ToolbarAddButton').prop('isDisabled')).toBe(true);
    expect(wrapper.find('Button[variant="secondary"]').prop('isDisabled')).toBe(
      true
    );
  });
});
