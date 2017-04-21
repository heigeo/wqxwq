define({
    'name': 'wqxwq_context',
    'init': function(config) {
        this.config = config;
        var app = this.app;
        config.icons.forEach(function(icon) {
            app.plugins.map.createIcon(
                icon.name, {'iconUrl': icon.url}
            );
        });
    },
    'context': function() {
        return {
            'project_name': this.config.project_name
        };
    }
})
