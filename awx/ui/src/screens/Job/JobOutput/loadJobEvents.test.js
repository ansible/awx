import { mockMissingEvents } from './loadJobEvents';

describe('mockMissingEvents', () => {
  test('should return back events', () => {
    const events = [
      { counter: 30 },
      { counter: 31 },
      { counter: 32 },
      { counter: 33 },
      { counter: 34 },
      { counter: 35 },
    ];
    expect(mockMissingEvents(events, 30, 35)).toEqual(events);
  });

  test('should mock missing events', () => {
    const events = [
      { counter: 30 },
      { counter: 31 },
      { counter: 33 },
      { counter: 35 },
    ];
    expect(mockMissingEvents(events, 30, 35)).toEqual([
      { counter: 30 },
      { counter: 31 },
      { counter: 32, stdout: '' },
      { counter: 33 },
      { counter: 34, stdout: '' },
      { counter: 35 },
    ]);
  });

  test('should mock multiple events in a row', () => {
    const events = [{ counter: 30 }, { counter: 31 }, { counter: 35 }];
    expect(mockMissingEvents(events, 30, 35)).toEqual([
      { counter: 30 },
      { counter: 31 },
      { counter: 32, stdout: '' },
      { counter: 33, stdout: '' },
      { counter: 34, stdout: '' },
      { counter: 35 },
    ]);
  });

  test('should mock events at beginning of array', () => {
    const events = [{ counter: 33 }, { counter: 34 }, { counter: 35 }];
    expect(mockMissingEvents(events, 31, 35)).toEqual([
      { counter: 31, stdout: '' },
      { counter: 32, stdout: '' },
      { counter: 33 },
      { counter: 34 },
      { counter: 35 },
    ]);
  });

  test('should mock events at end of array', () => {
    const events = [{ counter: 30 }, { counter: 31 }, { counter: 32 }];
    expect(mockMissingEvents(events, 30, 35)).toEqual([
      { counter: 30 },
      { counter: 31 },
      { counter: 32 },
      { counter: 33, stdout: '' },
      { counter: 34, stdout: '' },
      { counter: 35, stdout: '' },
    ]);
  });

  test('should mock if no events given', () => {
    expect(mockMissingEvents([], 30, 35)).toEqual([
      { counter: 30, stdout: '' },
      { counter: 31, stdout: '' },
      { counter: 32, stdout: '' },
      { counter: 33, stdout: '' },
      { counter: 34, stdout: '' },
      { counter: 35, stdout: '' },
    ]);
  });

  test('should preserve events before startCounter', () => {
    const events = [
      { counter: 27 },
      { counter: 28 },
      { counter: 30 },
      { counter: 31 },
      { counter: 32 },
    ];
    expect(mockMissingEvents(events, 30, 32)).toEqual([
      { counter: 27 },
      { counter: 28 },
      { counter: 30 },
      { counter: 31 },
      { counter: 32 },
    ]);
  });

  test('should preserve events after endCounter', () => {
    const events = [
      { counter: 33 },
      { counter: 34 },
      { counter: 35 },
      { counter: 37 },
    ];
    expect(mockMissingEvents(events, 31, 35)).toEqual([
      { counter: 31, stdout: '' },
      { counter: 32, stdout: '' },
      { counter: 33 },
      { counter: 34 },
      { counter: 35 },
      { counter: 37 },
    ]);
  });
});
