import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import LoggingTestAlert from './LoggingTestAlert';

describe('LoggingTestAlert', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('renders expected content when test is successful', () => {
    wrapper = mountWithContexts(
      <LoggingTestAlert
        successResponse={{}}
        errorResponse={null}
        onClose={() => {}}
      />
    );
    expect(wrapper.find('b#test-message').text()).toBe(
      'Log aggregator test sent successfully.'
    );
  });

  test('renders expected content when test is unsuccessful', () => {
    wrapper = mountWithContexts(
      <LoggingTestAlert
        successResponse={null}
        errorResponse={{
          response: {
            data: {
              error: 'Name or service not known',
            },
            status: 400,
            statusText: 'Bad Response',
          },
        }}
        onClose={() => {}}
      />
    );
    expect(wrapper.find('b#test-message').text()).toBe('Bad Response: 400');
    expect(wrapper.find('p#test-error').text()).toBe(
      'Name or service not known'
    );
  });

  test('close button should call "onClose"', () => {
    const onClose = jest.fn();
    expect(onClose).toHaveBeenCalledTimes(0);
    wrapper = mountWithContexts(
      <LoggingTestAlert
        successResponse={{}}
        errorResponse={null}
        onClose={onClose}
      />
    );
    wrapper.find('AlertActionCloseButton').invoke('onClose')();
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
