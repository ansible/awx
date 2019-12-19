import reducer, { initReducer } from './reducer';

describe('Lookup reducer', () => {
  describe('SELECT_ITEM', () => {
    it('should add item to selected items (multiple select)', () => {
      const state = {
        selectedItems: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'SELECT_ITEM',
        item: { id: 2 },
      });
      expect(result).toEqual({
        selectedItems: [{ id: 1 }, { id: 2 }],
        multiple: true,
      });
    });

    it('should not duplicate item if already selected (multiple select)', () => {
      const state = {
        selectedItems: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'SELECT_ITEM',
        item: { id: 1 },
      });
      expect(result).toEqual({
        selectedItems: [{ id: 1 }],
        multiple: true,
      });
    });

    it('should replace selected item (single select)', () => {
      const state = {
        selectedItems: [{ id: 1 }],
        multiple: false,
      };
      const result = reducer(state, {
        type: 'SELECT_ITEM',
        item: { id: 2 },
      });
      expect(result).toEqual({
        selectedItems: [{ id: 2 }],
        multiple: false,
      });
    });

    it('should not duplicate item if already selected (single select)', () => {
      const state = {
        selectedItems: [{ id: 1 }],
        multiple: false,
      };
      const result = reducer(state, {
        type: 'SELECT_ITEM',
        item: { id: 1 },
      });
      expect(result).toEqual({
        selectedItems: [{ id: 1 }],
        multiple: false,
      });
    });
  });

  describe('DESELECT_ITEM', () => {
    it('should de-select item (multiple)', () => {
      const state = {
        selectedItems: [{ id: 1 }, { id: 2 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'DESELECT_ITEM',
        item: { id: 1 },
      });
      expect(result).toEqual({
        selectedItems: [{ id: 2 }],
        multiple: true,
      });
    });

    it('should not change list if item not selected (multiple)', () => {
      const state = {
        selectedItems: [{ id: 1 }, { id: 2 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'DESELECT_ITEM',
        item: { id: 3 },
      });
      expect(result).toEqual({
        selectedItems: [{ id: 1 }, { id: 2 }],
        multiple: true,
      });
    });

    it('should de-select item (single select)', () => {
      const state = {
        selectedItems: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'DESELECT_ITEM',
        item: { id: 1 },
      });
      expect(result).toEqual({
        selectedItems: [],
        multiple: true,
      });
    });
  });

  describe('TOGGLE_MODAL', () => {
    it('should open the modal (single)', () => {
      const state = {
        isModalOpen: false,
        selectedItems: [],
        value: { id: 1 },
        multiple: false,
      };
      const result = reducer(state, {
        type: 'TOGGLE_MODAL',
      });
      expect(result).toEqual({
        isModalOpen: true,
        selectedItems: [{ id: 1 }],
        value: { id: 1 },
        multiple: false,
      });
    });

    it('should set null value to empty array', () => {
      const state = {
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: null,
        multiple: false,
      };
      const result = reducer(state, {
        type: 'TOGGLE_MODAL',
      });
      expect(result).toEqual({
        isModalOpen: true,
        selectedItems: [],
        value: null,
        multiple: false,
      });
    });

    it('should open the modal (multiple)', () => {
      const state = {
        isModalOpen: false,
        selectedItems: [],
        value: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'TOGGLE_MODAL',
      });
      expect(result).toEqual({
        isModalOpen: true,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      });
    });

    it('should close the modal', () => {
      const state = {
        isModalOpen: true,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'TOGGLE_MODAL',
      });
      expect(result).toEqual({
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      });
    });
  });

  describe('CLOSE_MODAL', () => {
    it('should close the modal', () => {
      const state = {
        isModalOpen: true,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'CLOSE_MODAL',
      });
      expect(result).toEqual({
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      });
    });
  });

  describe('SET_MULTIPLE', () => {
    it('should set multiple to true', () => {
      const state = {
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: false,
      };
      const result = reducer(state, {
        type: 'SET_MULTIPLE',
        value: true,
      });
      expect(result).toEqual({
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      });
    });

    it('should set multiple to false', () => {
      const state = {
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'SET_MULTIPLE',
        value: false,
      });
      expect(result).toEqual({
        isModalOpen: false,
        selectedItems: [{ id: 1 }],
        value: [{ id: 1 }],
        multiple: false,
      });
    });
  });

  describe('SET_VALUE', () => {
    it('should set the value', () => {
      const state = {
        value: [{ id: 1 }],
        multiple: true,
      };
      const result = reducer(state, {
        type: 'SET_VALUE',
        value: [{ id: 3 }],
      });
      expect(result).toEqual({
        value: [{ id: 3 }],
        multiple: true,
      });
    });
  });
});

describe('initReducer', () => {
  it('should init', () => {
    const state = initReducer({
      value: [],
      multiple: true,
      required: true,
    });
    expect(state).toEqual({
      selectedItems: [],
      value: [],
      multiple: true,
      isModalOpen: false,
      required: true,
    });
  });
});
