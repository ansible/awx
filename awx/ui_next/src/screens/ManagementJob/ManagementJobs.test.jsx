import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ManagementJobs from './ManagementJobs';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<ManagementJobs />', () => {
  let pageWrapper;
  let pageSections;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<ManagementJobs />);
    pageSections = pageWrapper.find('PageSection');
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('renders ok', () => {
    expect(pageWrapper.length).toBe(1);
    expect(pageWrapper.find('ScreenHeader').length).toBe(1);
    expect(pageSections.length).toBe(1);
  });
});
