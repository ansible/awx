import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import useThrottle from './useThrottle';

function TestInner() {
  return <div />;
}
function Test({ value }) {
  const throttled = useThrottle(value, 500);
  return <TestInner throttled={throttled} />;
}

jest.useFakeTimers();

describe('useThrottle', () => {
  test.skip('should throttle value', async () => {
    const mockTime = { value: 1000 };
    const realDateNow = Date.now.bind(global.Date);
    const dateNowStub = jest.fn(() => mockTime.value);
    global.Date.now = dateNowStub;
    let wrapper;
    await act(async () => {
      wrapper = await mount(<Test value={3} />);
    });

    wrapper.setProps({
      value: 4,
    });

    expect(wrapper.find('TestInner').prop('throttled')).toEqual(3);
    jest.advanceTimersByTime(501);
    mockTime.value = 1510;
    wrapper.setProps({
      value: 2,
    });
    wrapper.setProps({
      value: 4,
    });
    wrapper.update();
    expect(wrapper.find('TestInner').prop('throttled')).toEqual(4);

    // Date.now.restore();
    global.Date.now = realDateNow;
  });
});
