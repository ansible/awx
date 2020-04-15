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
  test('testing errors', () => {
    const wrapper = mountWithContexts(
      <ErrorDetail
        error={
          new Error({
            response: {
              config: {
                method: 'patch',
              },
              data: {
                project: ['project error'],
                inventory: ['inventory error'],
              },
            },
          })
        }
      />
    );
    wrapper.find('Expandable').prop('onToggle')();
    wrapper.update();
  });
});
