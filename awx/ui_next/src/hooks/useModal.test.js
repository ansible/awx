import React from 'react';
import { act } from 'react-dom/test-utils';
import { mount } from 'enzyme';
import useModal from './useModal';

const TestHook = ({ callback }) => {
  callback();
  return null;
};

const testHook = (callback) => {
  mount(<TestHook callback={callback} />);
};

describe('useModal hook', () => {
  let closeModal;
  let isModalOpen;
  let toggleModal;

  test('isModalOpen should return expected default value', () => {
    testHook(() => {
      ({ isModalOpen, toggleModal, closeModal } = useModal());
    });
    expect(isModalOpen).toEqual(false);
    expect(toggleModal).toBeInstanceOf(Function);
    expect(closeModal).toBeInstanceOf(Function);
  });

  test('isModalOpen should return expected initialized value', () => {
    testHook(() => {
      ({ isModalOpen, toggleModal, closeModal } = useModal(true));
    });
    expect(isModalOpen).toEqual(true);
    expect(toggleModal).toBeInstanceOf(Function);
    expect(closeModal).toBeInstanceOf(Function);
  });

  test('should return expected isModalOpen value after modal toggle', () => {
    testHook(() => {
      ({ isModalOpen, toggleModal, closeModal } = useModal());
    });
    expect(isModalOpen).toEqual(false);
    act(() => {
      toggleModal();
    });
    expect(isModalOpen).toEqual(true);
  });

  test('isModalOpen should be false after closeModal is called', () => {
    testHook(() => {
      ({ isModalOpen, toggleModal, closeModal } = useModal());
    });
    expect(isModalOpen).toEqual(false);
    act(() => {
      toggleModal();
    });
    expect(isModalOpen).toEqual(true);
    act(() => {
      closeModal();
    });
    expect(isModalOpen).toEqual(false);
  });
});
