import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ContentError from './ContentError';

describe('ContentError', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<ContentError />);
    expect(wrapper).toHaveLength(1);
  });
});
