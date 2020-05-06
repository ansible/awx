import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Pagination from './Pagination';

describe('Pagination', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<Pagination itemCount={0} max={9000} />);
    expect(wrapper).toHaveLength(1);
  });
});
