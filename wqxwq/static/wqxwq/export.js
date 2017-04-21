define({
    'context': function() {
        return {
            'current_year': new Date().getFullYear()
        };
    },
    'init': function() {
        $('body').on('submit', '.ui-popup form', function(evt) {
            require('wq/spinner').start(null, 2);
        });
    }
});
