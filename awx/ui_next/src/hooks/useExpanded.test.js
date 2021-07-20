import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import useExpanded from './useExpanded';

const array = [{ id: '1' }, { id: '2' }, { id: '3' }];

const TestHook = ({ callback }) => {
  callback();
  return null;
};

const testHook = (callback) => {
  mount(<TestHook callback={callback} />);
};

describe('useSelected hook', () => {
  let expanded;
  let isAllExpanded;
  let handleExpand;
  let setExpanded;
  let expandAll;

  test('should return expected initial values', () => {
    testHook(() => {
      ({ expanded, isAllExpanded, handleExpand, setExpanded, expandAll } =
        useExpanded());
    });
    expect(expanded).toEqual([]);
    expect(isAllExpanded).toEqual(false);
    expect(handleExpand).toBeInstanceOf(Function);
    expect(setExpanded).toBeInstanceOf(Function);
  });

  test('handleSelect should update and filter selected items', () => {
    testHook(() => {
      ({ expanded, isAllExpanded, handleExpand, setExpanded, expandAll } =
        useExpanded());
    });

    act(() => {
      handleExpand(array[0]);
    });
    expect(expanded).toEqual([array[0]]);

    act(() => {
      handleExpand(array[0]);
    });
    expect(expanded).toEqual([]);
  });

  test('should return expected isAllSelected value', () => {
    testHook(() => {
      ({ expanded, isAllExpanded, handleExpand, setExpanded, expandAll } =
        useExpanded(array));
    });

    act(() => {
      handleExpand(array[0]);
    });
    expect(expanded).toEqual([array[0]]);
    expect(isAllExpanded).toEqual(false);

    act(() => {
      handleExpand(array[1]);
      handleExpand(array[2]);
    });
    expect(expanded).toEqual(array);
    expect(isAllExpanded).toEqual(true);

    act(() => {
      setExpanded([]);
    });
    expect(expanded).toEqual([]);
    expect(isAllExpanded).toEqual(false);
  });

  test('should return selectAll', () => {
    testHook(() => {
      ({ expanded, isAllExpanded, handleExpand, setExpanded, expandAll } =
        useExpanded(array));
    });

    act(() => {
      expandAll(true);
    });
    expect(isAllExpanded).toEqual(true);
    expect(expanded).toEqual(array);

    act(() => {
      expandAll(false);
    });
    expect(isAllExpanded).toEqual(false);
    expect(expanded).toEqual([]);
  });
});
