import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';

import DataListCell from './DataListCell';

describe('DataListCell', () => {
  test('renders without failing', () => {
    const wrapper = mountWithContexts(<DataListCell />);
    expect(wrapper).toHaveLength(1);
  });
});
