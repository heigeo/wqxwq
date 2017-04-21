define({
    'name': 'project_name',
    'init': function(projectName) {
        this.project_name = projectName;
    },
    'context': function() {
        return {'project_name': this.project_name};
    }
})
