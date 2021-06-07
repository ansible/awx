import React from 'react';
import { mount } from 'enzyme';
import useDebounce from './useDebounce';

function TestInner() {
  return <div />;
}
function Test({ fn, delay = 500, data }) {
  const debounce = useDebounce(fn, delay);
  debounce(data);
  return <TestInner />;
}

test('useDebounce', () => {
  jest.useFakeTimers();
  const fn = jest.fn();
  mount(<Test fn={fn} data={{ data: 123 }} />);
  expect(fn).toHaveBeenCalledTimes(0);
  jest.advanceTimersByTime(510);
  expect(fn).toHaveBeenCalledTimes(1);
  expect(fn).toHaveBeenCalledWith({ data: 123 });
});
