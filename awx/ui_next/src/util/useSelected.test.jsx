import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import useSelected from './useSelected';

const array = [{ id: '1' }, { id: '2' }, { id: '3' }];

const TestHook = ({ callback }) => {
  callback();
  return null;
};

const testHook = callback => {
  mount(<TestHook callback={callback} />);
};

describe('useSelected hook', () => {
  let selected;
  let isAllSelected;
  let handleSelect;
  let setSelected;

  test('should return expected initial values', () => {
    testHook(() => {
      ({ selected, isAllSelected, handleSelect, setSelected } = useSelected());
    });
    expect(selected).toEqual([]);
    expect(isAllSelected).toEqual(false);
    expect(handleSelect).toBeInstanceOf(Function);
    expect(setSelected).toBeInstanceOf(Function);
  });

  test('handleSelect should update and filter selected items', () => {
    testHook(() => {
      ({ selected, isAllSelected, handleSelect, setSelected } = useSelected());
    });

    act(() => {
      handleSelect(array[0]);
    });
    expect(selected).toEqual([array[0]]);

    act(() => {
      handleSelect(array[0]);
    });
    expect(selected).toEqual([]);
  });

  test('should return expected isAllSelected value', () => {
    testHook(() => {
      ({ selected, isAllSelected, handleSelect, setSelected } = useSelected(
        array
      ));
    });

    act(() => {
      handleSelect(array[0]);
    });
    expect(selected).toEqual([array[0]]);
    expect(isAllSelected).toEqual(false);

    act(() => {
      handleSelect(array[1]);
      handleSelect(array[2]);
    });
    expect(selected).toEqual(array);
    expect(isAllSelected).toEqual(true);

    act(() => {
      setSelected([]);
    });
    expect(selected).toEqual([]);
    expect(isAllSelected).toEqual(false);
  });
});
