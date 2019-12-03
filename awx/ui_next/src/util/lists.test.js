import { getAddedAndRemoved } from './lists';

const one = { id: 1 };
const two = { id: 2 };
const three = { id: 3 };

describe('getAddedAndRemoved', () => {
  test('should handle no original list', () => {
    const items = [one, two, three];
    expect(getAddedAndRemoved(null, items)).toEqual({
      added: items,
      removed: [],
    });
  });

  test('should list added item', () => {
    const original = [one, two];
    const current = [one, two, three];
    expect(getAddedAndRemoved(original, current)).toEqual({
      added: [three],
      removed: [],
    });
  });

  test('should list removed item', () => {
    const original = [one, two, three];
    const current = [one, three];
    expect(getAddedAndRemoved(original, current)).toEqual({
      added: [],
      removed: [two],
    });
  });

  test('should handle both added and removed together', () => {
    const original = [two];
    const current = [one, three];
    expect(getAddedAndRemoved(original, current)).toEqual({
      added: [one, three],
      removed: [two],
    });
  });

  test('should handle different list order', () => {
    const original = [three, two];
    const current = [one, two, three];
    expect(getAddedAndRemoved(original, current)).toEqual({
      added: [one],
      removed: [],
    });
  });
});
