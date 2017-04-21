define(['./report', './export', './context'], function(report, exportUtil, context) {
    var plugins = [report, exportUtil, context];
    function registerAll(app) {
        plugins.forEach(function(plugin) {
            app.use(plugin);
        });
    }
    return {
        'report': report,
        'export': exportUtil,
        'plugins': plugins,
        'registerAll': registerAll,
    }
});
