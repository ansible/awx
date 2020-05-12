import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ScheduleOccurrences from './ScheduleOccurrences';

describe('<ScheduleOccurrences>', () => {
  let wrapper;
  describe('At least two dates passed in', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <ScheduleOccurrences
          preview={{
            local: ['2020-03-16T00:00:00-04:00', '2020-03-30T00:00:00-04:00'],
            utc: ['2020-03-16T04:00:00Z', '2020-03-30T04:00:00Z'],
          }}
        />
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('Local option initially set', async () => {
      expect(wrapper.find('MultiButtonToggle').props().value).toBe('local');
    });
    test('It renders the correct number of dates', async () => {
      expect(wrapper.find('dd').children().length).toBe(2);
    });
    test('Clicking UTC button toggles the dates to utc', async () => {
      wrapper.find('button[aria-label="UTC"]').simulate('click');
      expect(wrapper.find('MultiButtonToggle').props().value).toBe('utc');
      expect(wrapper.find('dd').children().length).toBe(2);
      expect(
        wrapper
          .find('dd')
          .children()
          .at(0)
          .text()
      ).toBe('3/16/2020, 4:00:00 AM');
      expect(
        wrapper
          .find('dd')
          .children()
          .at(1)
          .text()
      ).toBe('3/30/2020, 4:00:00 AM');
    });
  });
  describe('Only one date passed in', () => {
    test('Component should not render chldren', async () => {
      wrapper = mountWithContexts(
        <ScheduleOccurrences
          preview={{
            local: ['2020-03-16T00:00:00-04:00'],
            utc: ['2020-03-16T04:00:00Z'],
          }}
        />
      );
      expect(wrapper.find('ScheduleOccurrences').children().length).toBe(0);
      wrapper.unmount();
    });
  });
});
