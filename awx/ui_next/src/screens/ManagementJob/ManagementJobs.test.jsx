import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ManagementJobs from './ManagementJobs';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<ManagementJobs />', () => {
  let pageWrapper;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<ManagementJobs />);
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
    expect(pageWrapper.find('ScreenHeader').length).toBe(1);
  });
});
