import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ActivityStreamDescription from './ActivityStreamDescription';

describe('ActivityStreamDescription', () => {
  test('initially renders succesfully', () => {
    const description = mountWithContexts(
      <ActivityStreamDescription activity={{}} />
    );
    expect(description.find('span').length).toBe(1);
  });
});
