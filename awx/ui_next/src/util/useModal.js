import { useState } from 'react';

/**
 * useModal hook provides a way to read and update modal visibility
 * Param: boolean that sets initial modal state
 * Returns: {
 *  isModalOpen: boolean that indicates if modal is open
 *  toggleModal: function that toggles the modal open and close
 *  closeModal: function that closes modal
 * }
 */

export default function useModal(isOpen = false) {
  const [isModalOpen, setIsModalOpen] = useState(isOpen);

  function toggleModal() {
    setIsModalOpen(!isModalOpen);
  }

  function closeModal() {
    setIsModalOpen(false);
  }

  return {
    isModalOpen,
    toggleModal,
    closeModal,
  };
}
