function ProjectsStrings (BaseString) {
    BaseString.call(this, 'projects');

    let t = this.t;
    let ns = this.projects;

    ns.deleteProject = {
        CONFIRM: t.s('Are you sure you want to delete this project?'),
        INVALIDATE: t.s('Doing so will invalidate the following:')
    };
}

ProjectsStrings.$inject = ['BaseStringService'];

export default ProjectsStrings;
