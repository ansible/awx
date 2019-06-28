import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';

import ErrorDetail from './ErrorDetail';

describe('ErrorDetail', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <ErrorDetail
        error={
          new Error({
            response: {
              config: {
                method: 'post',
              },
              data: 'An error occurred',
            },
          })
        }
      />
    );
    expect(wrapper).toHaveLength(1);
  });
});
