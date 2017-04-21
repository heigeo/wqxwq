define([
    'wq/map',
    'wq/photos',
    'wq/patterns',
    'wq/chartapp',
    'wq/progress',
    './report',
    './export',
    './context'
],
function() {
    var plugins = [].slice.call(arguments);
    function registerAll(app) {
        plugins.forEach(app.use);
    }
    return {
        'plugins': plugins,
        'registerAll': registerAll,
    }
});
