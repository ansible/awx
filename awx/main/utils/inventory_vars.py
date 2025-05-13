import logging
from typing import TypeAlias, Any

from awx.main.models import InventoryGroupVariablesWithHistory


var_value: TypeAlias = Any
update_queue: TypeAlias = list[tuple[int, var_value]]


logger = logging.getLogger('awx.api.inventory_import')


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
        self._update_queue: update_queue = []
        """
        A queue representing updates from inventory sources in the sequence of
        occurrence.

        The queue is realized as a list of two-tuples containing variable values
        and their originating inventory source. The last item of the list is
        considered the top of the queue, and holds the current value of the
        variable.
        """

    def reset(self) -> None:
        """Reset the variable by deleting its history."""
        self._update_queue = []

    def load(self, updates: update_queue) -> "InventoryVariable":
        """Load internal state from a list."""
        self._update_queue = updates
        return self

    def dump(self) -> update_queue:
        """Save internal state to a list."""
        return self._update_queue

    def update(self, value: var_value, invsrc_id: int) -> None:
        """
        Update the variable with a new value from an inventory source.

        Updating means that this source is moved to the top of the queue
        and `value` becomes the new current value.

        :param value: The new value of the variable.
        :param int invsrc_id: The inventory source of the new variable value.
        :return: None
        """
        logger.debug(f"InventoryVariable().update({value}, {invsrc_id}):")
        # Move this source to the front of the queue by first deleting a
        # possibly existing entry, and then add the new entry to the front.
        self.delete(invsrc_id)
        self._update_queue.append((invsrc_id, value))

    def delete(self, invsrc_id: int) -> None:
        """
        Delete an inventory source from the variable.

        :param int invsrc_id: The inventory source id.
        :return: None
        """
        data_index = self._get_invsrc_index(invsrc_id)
        # Remove last update from this source, if there was any.
        if data_index is not None:
            value = self._update_queue.pop(data_index)[1]
            logger.debug(f"InventoryVariable().delete({invsrc_id}): {data_index=} {value=}")

    def _get_invsrc_index(self, invsrc_id: int) -> int | None:
        """Return the inventory source's position in the queue, or `None`."""
        for i, entry in enumerate(self._update_queue):
            if entry[0] == invsrc_id:
                return i
        return None

    def _get_current_value(self) -> var_value:
        """
        Return the current value of the variable, or None if the variable has no
        history.
        """
        return self._update_queue[-1][1] if self._update_queue else None

    @property
    def value(self) -> var_value:
        """Read the current value of the variable."""
        return self._get_current_value()

    @property
    def has_no_source(self) -> bool:
        """True, if the variable is orphan, i.e. no source contains this var anymore."""
        return not self._update_queue

    def __str__(self):
        """Return the string representation of the current value."""
        return str(self.value or "")


class InventoryGroupVariables(dict):
    """
    Represent all inventory variables from one group.

    This dict contains all variables of a inventory group and their current
    value under consideration of the inventory source update history.

    Note that variables values cannot be `None`, use the empty string to
    indicate that a variable holds no value. See also `InventoryVariable`.
    """

    def __init__(self, id: int) -> None:
        """
        :param int id: The id of the group object.
        :return: None
        """
        super().__init__()
        self.id = id
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

    def load_state(self, state: dict[str, update_queue]) -> "InventoryGroupVariables":
        """Load internal state from a dict."""
        for name, updates in state.items():
            self._vars[name] = InventoryVariable(name).load(updates)
        self._sync_vars()
        return self

    def save_state(self) -> dict[str, update_queue]:
        """Return internal state as a dict."""
        state = {}
        for name, inv_var in self._vars.items():
            state[name] = inv_var.dump()
        return state

    def update_from_src(
        self,
        new_vars: dict[str, var_value],
        source_id: int,
        overwrite_vars: bool = True,
        reset: bool = False,
    ) -> None:
        """
        Update with variables from an inventory source.

        Delete all variables for this source which are not in the update vars.

        :param dict new_vars: The variables from the inventory source.
        :param int invsrc_id: The id of the inventory source for this update.
        :param bool overwrite_vars: If `True`, delete this source's history
            entry for variables which are not in this update. If `False`, keep
            the old updates in the history for such variables. Default is
            `True`.
        :param bool reset: If `True`, delete the update history for all existing
            variables before updating the new vars. Therewith making this update
            overwrite all history. Default is `False`.
        :return: None
        """
        logger.debug(f"InventoryGroupVariables({self.id}).update_from_src({new_vars=}, {source_id=}, {overwrite_vars=}, {reset=}): {self=}")
        # Create variables which are newly introduced by this source.
        for name in new_vars:
            if name not in self._vars:
                self._vars[name] = InventoryVariable(name)
        # Combine the names of the existing vars and the new vars from this update.
        all_var_names = list(set(list(self.keys()) + list(new_vars.keys())))
        # In reset-mode, delete all existing vars and their history before
        # updating.
        if reset:
            for name in all_var_names:
                self._vars[name].reset()
        # Go through all variables (the existing ones, and the ones added by
        # this update), delete this source from variables which are not in this
        # update, and update the value of variables which are part of this
        # update.
        for name in all_var_names:
            # Update or delete source from var (if name not in vars).
            if name in new_vars:
                self._vars[name].update(new_vars[name], source_id)
            elif overwrite_vars:
                self._vars[name].delete(source_id)
            # Delete vars which have no source anymore.
            if self._vars[name].has_no_source:
                del self._vars[name]
                del self[name]
        # After the update, refresh the internal dict with the possibly changed
        # current values.
        self._sync_vars()
        logger.debug(f"InventoryGroupVariables({self.id}).update_from_src(): {self=}")


def update_group_variables(
    group_id: int | None,
    newvars: dict,
    dbvars: dict | None,
    invsrc_id: int,
    inventory_id: int,
    overwrite_vars: bool = True,
    reset: bool = False,
) -> dict[str, var_value]:
    """
    Update the inventory variables of one group.

    Merge the new variables into the existing group variables.

    The update can be triggered either by an inventory update via API, or via a
    manual edit of the variables field in the awx inventory form.

    TODO: Can we get rid of the dbvars? This is only needed because the new
    update-var mechanism needs to be properly initialized if the db already
    contains some variables.

    :param int group_id: The inventory group id (pk). For the 'all'-group use
        `None`, because this group is not an actual `Group` object in the
        database.
    :param dict newvars: The variables contained in this update.
    :param dict dbvars: The variables which are already stored in the database
        for this inventory and this group. Can be `None`.
    :param int invsrc_id: The id of the inventory source. Usually this is the
        database primary key of the inventory source object, but there is one
        special id -1 which is used for the initial update from the database and
        for manual updates via the GUI.
    :param int inventory_id: The id of the inventory on which this update is
        applied.
    :param bool overwrite_vars: If `True`, delete variables which were merged
        from the same source in a previous update, but are no longer contained
        in that source. If `False`, such variables would not be removed from the
        group. Default is `True`.
    :param bool reset: If `True`, delete all variables from previous updates,
        therewith making this update overwrite all history. Default is `False`.
    :return: The variables and their current values as a dict.
    :rtype: dict
    """
    inv_group_vars = InventoryGroupVariables(group_id)
    # Restore the existing variables state.
    try:
        # Get the object for this group from the database.
        model = InventoryGroupVariablesWithHistory.objects.get(inventory_id=inventory_id, group_id=group_id)
    except InventoryGroupVariablesWithHistory.DoesNotExist:
        # If no previous state exists, create a new database object, and
        # initialize it with the current group variables.
        model = InventoryGroupVariablesWithHistory(inventory_id=inventory_id, group_id=group_id)
        if dbvars:
            inv_group_vars.update_from_src(dbvars, -1)  # Assume -1 as inv_source_id for existing vars.
    else:
        # Load the group variables state from the database object.
        inv_group_vars.load_state(model.variables)
    #
    logger.debug(f"update_group_variables: before update_from_src {model.variables=}")
    # Apply the new inventory update onto the group variables.
    inv_group_vars.update_from_src(newvars, invsrc_id, overwrite_vars, reset)
    # Save the new variables state.
    model.variables = inv_group_vars.save_state()
    model.save()
    logger.debug(f"update_group_variables: after update_from_src {model.variables=}")
    logger.debug(f"update_group_variables({group_id=}, {newvars}): {inv_group_vars}")
    return inv_group_vars
