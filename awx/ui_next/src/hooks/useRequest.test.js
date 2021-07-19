import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import { mountWithContexts } from '../../testUtils/enzymeHelpers';
import useRequest, { useDeleteItems } from './useRequest';

function TestInner() {
  return <div />;
}
function Test({ makeRequest, initialValue = {} }) {
  const request = useRequest(makeRequest, initialValue);
  return <TestInner {...request} />;
}
function DeleteTest({ makeRequest, args = {} }) {
  const request = useDeleteItems(makeRequest, args);
  return <TestInner {...request} />;
}

describe('useRequest hooks', () => {
  describe('useRequest', () => {
    test('should return initial value as result', async () => {
      const makeRequest = jest.fn();
      makeRequest.mockResolvedValue({ data: 'foo' });
      const wrapper = mount(
        <Test
          makeRequest={makeRequest}
          initialValue={{
            initial: true,
          }}
        />
      );

      expect(wrapper.find('TestInner').prop('result')).toEqual({
        initial: true,
      });
    });

    test('should return result', async () => {
      const makeRequest = jest.fn();
      makeRequest.mockResolvedValue({ data: 'foo' });
      const wrapper = mount(<Test makeRequest={makeRequest} />);

      await act(async () => {
        wrapper.find('TestInner').invoke('request')();
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('result')).toEqual({ data: 'foo' });
    });

    test('should is isLoading flag', async () => {
      const makeRequest = jest.fn();
      let resolve;
      const promise = new Promise(r => {
        resolve = r;
      });
      makeRequest.mockReturnValue(promise);
      const wrapper = mount(<Test makeRequest={makeRequest} />);

      await act(async () => {
        wrapper.find('TestInner').invoke('request')();
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('isLoading')).toEqual(true);
      await act(async () => {
        resolve({ data: 'foo' });
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('isLoading')).toEqual(false);
      expect(wrapper.find('TestInner').prop('result')).toEqual({ data: 'foo' });
    });

    test('should invoke request function', async () => {
      const makeRequest = jest.fn();
      makeRequest.mockResolvedValue({ data: 'foo' });
      const wrapper = mount(<Test makeRequest={makeRequest} />);

      expect(makeRequest).not.toHaveBeenCalled();
      await act(async () => {
        wrapper.find('TestInner').invoke('request')();
      });
      wrapper.update();
      expect(makeRequest).toHaveBeenCalledTimes(1);
    });

    test('should return error thrown from request function', async () => {
      const error = new Error('error');
      const makeRequest = () => {
        throw error;
      };
      const wrapper = mount(<Test makeRequest={makeRequest} />);

      await act(async () => {
        wrapper.find('TestInner').invoke('request')();
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('error')).toEqual(error);
    });

    test('should reset error/result on each request', async () => {
      const error = new Error('error');
      const makeRequest = throwError => {
        if (throwError) {
          throw error;
        }

        return { data: 'foo' };
      };
      const wrapper = mount(<Test makeRequest={makeRequest} />);

      await act(async () => {
        wrapper.find('TestInner').invoke('request')(true);
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('result')).toEqual({});
      expect(wrapper.find('TestInner').prop('error')).toEqual(error);
      await act(async () => {
        wrapper.find('TestInner').invoke('request')();
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('result')).toEqual({ data: 'foo' });
      expect(wrapper.find('TestInner').prop('error')).toEqual(null);
      await act(async () => {
        wrapper.find('TestInner').invoke('request')(true);
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('result')).toEqual({});
      expect(wrapper.find('TestInner').prop('error')).toEqual(error);
    });

    test('should not update state after unmount', async () => {
      const makeRequest = jest.fn();
      let resolve;
      const promise = new Promise(r => {
        resolve = r;
      });
      makeRequest.mockReturnValue(promise);
      const wrapper = mount(<Test makeRequest={makeRequest} />);

      expect(makeRequest).not.toHaveBeenCalled();
      await act(async () => {
        wrapper.find('TestInner').invoke('request')();
      });
      wrapper.unmount();
      await act(async () => {
        resolve({ data: 'foo' });
      });
    });
  });

  describe('useDeleteItems', () => {
    test('should invoke delete function', async () => {
      const makeRequest = jest.fn();
      makeRequest.mockResolvedValue({ data: 'foo' });
      const wrapper = mountWithContexts(
        <DeleteTest
          makeRequest={makeRequest}
          args={{
            qsConfig: {},
            fetchItems: () => {},
          }}
        />
      );

      expect(makeRequest).not.toHaveBeenCalled();
      await act(async () => {
        wrapper.find('TestInner').invoke('deleteItems')();
      });
      wrapper.update();
      expect(makeRequest).toHaveBeenCalledTimes(1);
    });

    test('should return error object thrown by function', async () => {
      const error = new Error('error');
      const makeRequest = () => {
        throw error;
      };
      const wrapper = mountWithContexts(
        <DeleteTest
          makeRequest={makeRequest}
          args={{
            qsConfig: {},
            fetchItems: () => {},
          }}
        />
      );

      await act(async () => {
        wrapper.find('TestInner').invoke('deleteItems')();
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('deletionError')).toEqual(error);
    });

    test('should dismiss error', async () => {
      const error = new Error('error');
      const makeRequest = () => {
        throw error;
      };
      const wrapper = mountWithContexts(
        <DeleteTest
          makeRequest={makeRequest}
          args={{
            qsConfig: {},
            fetchItems: () => {},
          }}
        />
      );

      await act(async () => {
        wrapper.find('TestInner').invoke('deleteItems')();
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('TestInner').invoke('clearDeletionError')();
      });
      wrapper.update();
      expect(wrapper.find('TestInner').prop('deletionError')).toEqual(null);
    });
  });
});
