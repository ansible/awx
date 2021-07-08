import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ActivityStream from './ActivityStream';

jest.mock('../../api');

describe('<ActivityStream />', () => {
  test('initially renders without crashing', async () => {
    let pageWrapper;
    await act(async () => {
      pageWrapper = await mountWithContexts(<ActivityStream />);
    });
    expect(pageWrapper.length).toBe(1);
  });
});
