import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import JobEventSkeleton from './JobEventSkeleton';

const contentSelector = 'JobEventSkeletonContent';

describe('<JobEvenSkeletont />', () => {
  test('initially renders successfully', () => {
    const wrapper = mountWithContexts(
      <JobEventSkeleton contentLength={80} counter={100} />
    );
    expect(wrapper.find(contentSelector).length).toEqual(1);
  });

  test('always skips first counter', () => {
    const wrapper = mountWithContexts(
      <JobEventSkeleton contentLength={80} counter={1} />
    );
    expect(wrapper.find(contentSelector).length).toEqual(0);
  });
});
