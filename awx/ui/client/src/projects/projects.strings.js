function ProjectsStrings (BaseString) {
    BaseString.call(this, 'projects');

    let t = this.t;
    let ns = this.projects;

    ns.deleteProject = {
        CONFIRM: t.s('The project is currently being used by other resources. Are you sure you want to delete this project?')
    };
}

ProjectsStrings.$inject = ['BaseStringService'];

export default ProjectsStrings;
