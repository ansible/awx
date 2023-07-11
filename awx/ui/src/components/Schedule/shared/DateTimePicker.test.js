import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import DateTimePicker from './DateTimePicker';

describe('<DateTimePicker/>', () => {
  let wrapper;
  test('should render properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{ startDate: '2021-05-26', startTime: '2:15 PM' }}
        >
          <DateTimePicker
            dateFieldName="startDate"
            timeFieldName="startTime"
            label="Start date/time"
          />
        </Formik>
      );
    });
    expect(wrapper.find('DatePicker')).toHaveLength(1);
    expect(wrapper.find('DatePicker').prop('value')).toBe('2021-05-26');
    expect(wrapper.find('TimePicker')).toHaveLength(1);
    expect(wrapper.find('TimePicker').prop('value')).toBe('2:15 PM');
  });
  test('should update values properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{ startDate: '2021-05-26', startTime: '2:15 PM' }}
        >
          <DateTimePicker
            dateFieldName="startDate"
            timeFieldName="startTime"
            label="Start date/time"
          />
        </Formik>
      );
    });

    await act(async () => {
      wrapper.find('DatePicker').prop('onChange')(
        null,
        '2021-05-29',
        new Date('Sat May 29 2021 00:00:00 GMT-0400 (Eastern Daylight Time)')
      );
      wrapper.find('TimePicker').prop('onChange')(null, '7:15 PM');
    });
    wrapper.update();
    expect(wrapper.find('DatePicker').prop('value')).toBe('2021-05-29');
    expect(wrapper.find('TimePicker').prop('value')).toBe('7:15 PM');
  });
});
