import logging
import os
import json
from typing import TypeAlias


var_value: TypeAlias = str | int
update_queue: TypeAlias = list[tuple[int, var_value]]


# logger = logging.getLogger('awx.main.commands.inventory_import')
logger = logging.getLogger('awx.api.inventory_import')  # DJDEBUG logger above doesn't show up in docker-compose awx...


class InventoryVariable:
    """
    Represents an inventory variable.

    This class keeps track of the variable updates from different inventory
    sources.

    An inventory variable cannot hold the value `None`. To indicate that the
    variable holds no value, the empty string has to be used. See also the
    documentation of method `update`.
    """

    def __init__(self, name: str) -> None:
        """
        :param str name: The variable's name.
        :return: None
        """
        self.name = name
        self._update_queue: update_queue = []
        """
        A queue representing updates from inventory sources in the sequence of
        occurrence.

        The queue is realized as a list of two-tuples containing variable values
        and their originating inventory source. The last item of the list is
        considered the top of the queue, and holds the current value of the
        variable.
        """

    def load(self, updates: update_queue) -> "InventoryVariable":
        """Load internal state from a dict."""
        self._update_queue = updates
        return self

    def dump(self) -> update_queue:
        """Save internal state to a dict."""
        return self._update_queue

    def update(self, value: var_value | None, invsrc_id: int) -> None:
        """
        Update the variable with a new value from an inventory source.

        If `value` is not `None`, it becomes the new current value. Otherwise
        the current value is not changed, and this source is removed from the
        list of sources for this variable.

        In other words:

        If `value` is `None`, delete this update from the update queue. The
        current value is not changed.

        If `value` is not `None`, this source is moved to the top of the queue
        and `value` becomes the new current value.

        :param value: The new value of the variable. If None, no value is set
            and the source is removed from this variable.

            .. Note::

                If `source_id` is 0 (indicating that the variable is set from an
                inventory-level edit), the update queue is deleted completely.
                Find the rational for this design in the description of
                `InventoryGroupVariables.update_from_src`.

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
        elif invsrc_id == 0:
            # Delete all updates if the variable has been deleted on
            # inventory-level.
            self._update_queue = []

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
        """True, if the variable is orphan, i.e. no source contains this var anymore."""
        return not self._update_queue

    def __str__(self):
        """Return the string representation of the current value."""
        return str(self.value)


class InventoryGroupVariables(dict):
    """
    Represent all inventory variables from one group.

    This dict contains all variables of a inventory group and their current
    value under consideration of the inventory source update history.

    Note that variables values cannot be `None`, use the empty string to
    indicate that a variable holds no value. See also `InventoryVariable`.
    """

    def __init__(self, name: str = "") -> None:
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

    def _sync_vars(self) -> None:
        """
        Copy the current values of all variables into the internal dict.

        Call this everytime the `_vars` structure has been modified.
        """
        for name, inv_var in self._vars.items():
            self[name] = inv_var.value

    def load(self, state: dict[str, update_queue]) -> None:
        """Load internal state from a dict."""
        for name, updates in state.items():
            self._vars[name] = InventoryVariable(name).load(updates)
        self._sync_vars()

    def dump(self) -> dict[str, update_queue]:
        """Return internal state as a dict."""
        state = {}
        for name, inv_var in self._vars.items():
            state[name] = inv_var.dump()
        return state

    def update_from_src(self, vars: dict[str, var_value], source_id: int) -> None:
        """
        Update with variables from an inventory source.

        Delete all variables for this source which are not in the update vars.

        .. Note::

            If the source_id indicates the special case that the update is
            caused by an inventory-level object edit (id = 0), vars which are
            not contained in the update are deleted together with their update
            history.

            We do this because if a variable is not contained in an
            inventory-level update, it must have been explicitely deleted from
            the inventory form field. This indicates that the operator expects
            the variable to be removed from the group, and not that it reappears
            with the value from the previous source update.

        :param dict vars: The variables from the inventory source.
        :param int invsrc_id: The id of the inventory source for this update.
        :return: None
        """
        logger.error(f"InventoryGroupVariables({self.name}).update_from_src({vars=}, {source_id=}): {self=}")
        # Create variables which are newly introduced by this source.
        for name in vars:
            if name not in self._vars:
                self._vars[name] = InventoryVariable(name)
        # Combine the names of the existing vars and the new vars from this update.
        all_var_names = list(set(list(self.keys()) + list(vars.keys())))
        # Go through all variables (the existing ones, and the ones added by
        # this update), delete this source from variables which are not in this
        # update, and update the value of variables which are part of this
        # update.
        for name in all_var_names:
            # Update or delete source from var (if name not in vars).
            self._vars[name].update(vars.get(name), source_id)
            # Delete vars which have no source anymore.
            if self._vars[name].has_no_source:
                del self._vars[name]
                del self[name]
        # After the update, refresh the internal dict with the possibly changed
        # current values.
        self._sync_vars()
        logger.error(f"InventoryGroupVariables({self.name}).update_from_src(): {self=}")


def update_group_variables(group: str, newvars: dict, dbvars: dict | None, invsrc_id: int) -> dict:
    """
    Update the inventory variables of one group.

    The update can be triggered either by an inventory update via API, or via a
    manual edit of the variables field in the awx inventory form.

    TODO: Can we get rid of the dbvars? This is only needed because the new
    update-var mechanism needs to be properly initialized if the db already
    contains some variables.

    :param str group: The inventory group name, or "all" for the all-group.
    :param dict newvars: The variables contained in this update.
    :param dict dbvars: (optional) The variables which are already stored in the
        database for this inventory and this group.
    :param int invsrc_id: The id of the inventory source. Usually this is the
        database pk of the inventory source object, but there are some special
        ids: -1 for the initial update from the database. 0 for manual updates.
    """
    inv_group_vars = InventoryGroupVariables(group)
    #
    filepath = f"/awx_devel/tmp/vars_{group}"
    #
    if not os.path.isfile(filepath):
        if dbvars:
            inv_group_vars.update_from_src(dbvars, -1)  # Assume -1 as inv_source_id for existing vars.
    else:
        with open(filepath, "r") as fp:
            inv_group_vars.load(json.load(fp))
    #
    inv_group_vars.update_from_src(newvars, invsrc_id)
    #
    with open(filepath, "w") as fp:
        json.dump(inv_group_vars.dump(), fp)
        fp.write("\n")
    #
    logger.error(f"update_group_variables({group}, {newvars}): {inv_group_vars}")
    return inv_group_vars


if __name__ == "__main__":
    import doctest

    doctest.testmod()
