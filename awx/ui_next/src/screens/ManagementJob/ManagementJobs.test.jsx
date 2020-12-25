import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ManagementJobs from './ManagementJobs';

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
    expect(pageWrapper.find('Breadcrumbs').length).toBe(1);
  });
});
