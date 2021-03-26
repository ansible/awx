import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import LineChart from './LineChart';

describe('<LineChart/>', () => {
  test('should render properly', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <LineChart
          data={[
            {
              name: 'Instance 1',
              values: [
                { x: 0, y: 10 },
                { x: 1, y: 20 },
                { x: 3, y: 30 },
              ],
            },
            {
              name: 'Instance 1',
              values: [
                { x: 0, y: 40 },
                { x: 1, y: 50 },
                { x: 3, y: 60 },
              ],
            },
          ]}
          helpText="This is the help text"
        />
      );
    });
    expect(wrapper.find('LineChart').length).toBe(1);
  });
});
