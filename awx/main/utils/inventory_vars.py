import logging
from typing import TypeAlias


var_value: TypeAlias = str | int

# logger = logging.getLogger('awx.main.commands.inventory_import')
logger = logging.getLogger('awx.api.inventory_import')  # DJDEBUG logger above doesn't show up in docker-compose awx...


class InventoryVariable:
    """
    Represents an inventory variable.

    This class keeps track of the variable updates from different inventory
    sources.
    """

    def __init__(self, name: str) -> None:
        """
        :param str name: The variable's name.
        :return: None
        """
        self.name = name
        self._update_queue: list[tuple[int, var_value]] = []
        """
        A queue representing updates from inventory sources in the sequence of
        occurrence.

        The queue is realized as a list of two-tuples containing variable values
        and their originating inventory source. The last item of the list is
        considered the top of the queue, and holds the current value of the
        variable.
        """

    def update(self, value: var_value | None, invsrc_id: int) -> None:
        """
        Update the variable with a new value from an inventory source.

        If `value` is not `None`, it becomes the new current value. Otherwise
        the current value is not changed, and this source is removed from the
        list of sources for this variable.

        In other words:

        If `value` is `None`, delete this update from the list of sources. The
        current value is not changed.

        If `value` is not `None`, this source is moved to the top of the queue
        and `value` becomes the new current value.

        :param value: The new value of the variable. If None, no value is set
            and the source is removed from this variable.

            .. Note:: Do we need to store variables with value None?

        :param int invsrc_id: The inventory source of the new variable value.
        :return: None
        """
        logger.error(f"InventoryVariable().update({value}, {invsrc_id}):")
        # Remove the existing entry for this inventory source in any case,
        # because we have to either bring it to the front of the queue (value is
        # not None) or we have to just delete it (value is None).
        self._delete(invsrc_id)
        # Add source from this update to the front of the queue, if it contains
        # this variable.
        if value is not None:
            self._update_queue.append((invsrc_id, value))

    def _delete(self, invsrc_id: int) -> None:
        """
        Delete an inventory source from the variable.

        :param int invsrc_id: The inventory source id.
        :return: None
        """
        data_index = self._get_invsrc_index(invsrc_id)
        # Remove last update from this source, if there was any.
        if data_index is not None:
            value = self._update_queue.pop(data_index)[1]
            logger.error(f"InventoryVariable().delete({invsrc_id}): {data_index=} {value=}")

    def _get_invsrc_index(self, invsrc_id: int) -> int | None:
        """Return the inventory source's position in the queue, or `None`."""
        for i, entry in enumerate(self._update_queue):
            if entry[0] == invsrc_id:
                return i
        return None

    def _get_current_value(self) -> var_value | None:
        """Return the current value of the variable, or None."""
        return self._update_queue[-1][1] if self._update_queue else None

    @property
    def value(self) -> var_value | None:
        """Read the current value of the variable."""
        return self._get_current_value()

    @property
    def has_no_source(self) -> bool:
        """
        True, if the variable is orphan, i.e. no source contains this var anymore.
        """
        return not self._update_queue

    def __str__(self):
        """Return the string representation of the current value."""
        return str(self.value)


class InventoryGroupVariables(dict):
    """
    Represent all inventory variables from one group.

    This dict contains all variables of a inventory group and their current
    value under consideration of the inventory source update history.
    """

    def __init__(self, name: str) -> None:
        """
        :param str name: The name of the group, 'all' for the all-group.
        :return: None
        """
        logger.error(f"InventoryGroupVariables().__init__({name}) >>>>")
        super().__init__()
        self.name = name
        # In _vars we keep all sources for a given variable. This enables us to
        # find the current value for a variable, which is the value from the
        # latest update which defined this variable.
        self._vars: dict[str, InventoryVariable] = {}

    def update_from_src(self, vars: dict[str, var_value], source_id: int) -> None:
        """
        Update with variables from an inventory source.

        Delete all variables for this source which are not in the update vars.

        :param dict vars: The variables from the inventory source.
        :param int invsrc_id: The id of the inventory source for this update.
        :return: None
        """
        logger.error(f"InventoryGroupVariables({self.name}).update_from_src({vars=}, {source_id=}): {self=}")
        # Combine the names of the existing vars and the new vars from this update.
        all_var_names = list(set(list(self.keys()) + list(vars.keys())))
        # Go through all variables (the existing ones, and the ones added by
        # this update), delete this source from variables which are not in this
        # update, and update the value of variables which are part of this
        # update.
        for name in all_var_names:
            if name not in self._vars:
                self._vars[name] = InventoryVariable(name)
            self._vars[name].update(vars.get(name), source_id)  # Update or delete (if name not in vars)
            # if name in vars:
            #     self._vars[name].update(vars.get(name), source_id)
            # else:
            #     self._vars[name].delete(source_id)
            # Delete vars which have no source anymore.
            if self._vars[name].has_no_source:
                del self._vars[name]
                del self[name]
        for name, inv_var in self._vars.items():
            self[name] = inv_var.value
        logger.error(f"InventoryGroupVariables({self.name}).update_from_src(): {self=}")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
