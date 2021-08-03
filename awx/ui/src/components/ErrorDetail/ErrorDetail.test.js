import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

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
    act(() => wrapper.find('ExpandableSection').prop('onToggle')());
    wrapper.update();
  });
});
