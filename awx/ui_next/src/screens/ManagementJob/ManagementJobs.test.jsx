import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ManagementJobs from './ManagementJobs';

describe('<ManagementJobs />', () => {
  let pageWrapper;
  let pageSections;

  beforeEach(() => {
    pageWrapper = mountWithContexts(<ManagementJobs />);
    pageSections = pageWrapper.find('PageSection');
  });

  test('renders ok', () => {
    expect(pageWrapper.length).toBe(1);
    expect(pageWrapper.find('ScreenHeader').length).toBe(1);
    expect(pageSections.length).toBe(1);
  });
});
