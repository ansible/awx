function ProjectsStrings (BaseString) {
    BaseString.call(this, 'projects');

    const { t } = this;
    const ns = this.projects;

    ns.list = {
        PANEL_TITLE: t.s('PROJECTS'),
        ROW_ITEM_LABEL_DESCRIPTION: t.s('DESCRIPTION'),
        ROW_ITEM_LABEL_REVISION: t.s('REVISION'),
        ROW_ITEM_LABEL_ORGANIZATION: t.s('ORGANIZATION'),
        ROW_ITEM_LABEL_MODIFIED: t.s('LAST MODIFIED'),
        ROW_ITEM_LABEL_USED: t.s('LAST USED'),
        ADD: t.s('Add a new project')
    };

    ns.update = {
        GET_LATEST: t.s('Get latest SCM revision'),
        UPDATE_RUNNING: t.s('SCM update currently running'),
        MANUAL_PROJECT_NO_UPDATE: t.s('Manual projects do not require an SCM update'),
        CANCEL_UPDATE_REQUEST: t.s('Your request to cancel the update was submitted to the task manager.'),
        NO_UPDATE_INFO: t.s('There is no SCM update information available for this project. An update has not yet been completed.  If you have not already done so, start an update for this project.'),
        NO_PROJ_SCM_CONFIG: t.s('The selected project is not configured for SCM. To configure for SCM, edit the project and provide SCM settings, and then run an update.'),
        NO_ACCESS_OR_COMPLETED_UPDATE: t.s('Either you do not have access or the SCM update process completed'),
        NO_RUNNING_UPDATE: t.s('An SCM update does not appear to be running for project: '),
    };

    ns.alert = {
        NO_UPDATE: t.s('No Updates Available'),
        UPDATE_CANCEL: t.s('SCM Update Cancel'),
        CANCEL_NOT_ALLOWED: t.s('Cancel Not Allowed'),
        NO_SCM_CONFIG: t.s('No SCM Configuration'),
        UPDATE_NOT_FOUND: t.s('Update Not Found'),
    };

    ns.status = {
        NOT_CONFIG: t.s('Not configured for SCM'),
        NEVER_UPDATE: t.s('No SCM updates have run for this project'),
        UPDATE_QUEUED: t.s('Update queued. Click for details'),
        UPDATE_RUNNING: t.s('Update running. Click for details'),
        UPDATE_SUCCESS: t.s('Update succeeded. Click for details'),
        UPDATE_FAILED: t.s('Update failed. Click for details'),
        UPDATE_MISSING: t.s('Update missing. Click for details'),
        UPDATE_CANCELED: t.s('Update canceled. Click for details'),
    };

    ns.error = {
        HEADER: this.error.HEADER,
        CALL: this.error.CALL,
    };
}

ProjectsStrings.$inject = ['BaseStringService'];

export default ProjectsStrings;
