import debounce from './debounce';

jest.useFakeTimers();

describe('debounce', () => {
  test('it debounces', () => {
    let count = 0;
    const func = increment => {
      count += increment;
    };
    const debounced = debounce(func, 1000);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    expect(count).toEqual(0);
    jest.advanceTimersByTime(1000);
    expect(count).toEqual(2);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    jest.advanceTimersByTime(1000);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    jest.advanceTimersByTime(1000);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    debounced(2);
    jest.advanceTimersByTime(1000);
    expect(count).toEqual(8);
  });
});
