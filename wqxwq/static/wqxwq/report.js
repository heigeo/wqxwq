define({
    'context': function(ctx, routeInfo) {
        if (routeInfo.page != 'report' || routeInfo.mode != 'edit') {
            return;
        }
        if (!routeInfo.params || !routeInfo.params.project_id) {
            return;
        }
        if (ctx.project) {
            return;
        }
        return {'project': {'slug': routeInfo.params.project_id}}; 
    },
    'run': function($page, routeInfo) {
        if (routeInfo.page != 'report' || routeInfo.mode != 'edit') {
            return;
        }
        var self = this;
        var idFields = [
            'event[site][slug]',
            // 'event[type][slug]',
            'event[depth]',
            'event[date]',
            'time'
        ];
        $page.on('change', 'select, input', function(evt) {
            if (idFields.indexOf(evt.currentTarget.name) != -1) {
                setActivityId();
            } else {
                var match = evt.currentTarget.name.match(/results\[(\d+)\]\[(\w+)\]/);
                if (match) {
                    if ($(evt.currentTarget).val() == "LOOKUP") {
                        lookupDomain(match[1], match[2]);
                    } else if (match[2] == 'type_id') {
                        setCharacteristic(match[1]);
                    } else if (match[2] == 'value') {
                        setValue(match[1]);
                    }
                }
            }
        });

        for (var i = 0; i < $page.find('.section-results').length; i++) {
            setCharacteristic(i);
            setValue(i);
        }

        function setActivityId() {
            var parts = idFields.map(function(fieldName) {
                var $field = $page.find("[name='" + fieldName + "']");
                return ($field.val() || "").replace(/\W/g, "");
            }).filter(function(val) {
                return val;
            });
            if (parts.length < 2) {
                return;
            }
            $page.find('[name=activity_id]').val(parts.join('-'));
        }
        
        var optCache = {};
        function setCharacteristic(index) {
            var cid = getField(index, 'type_id').val();
            self.app.models.characteristic.find(cid).then(function(chr) {
                if (!chr) {
                    return;
                }
                if (!optCache[index]) {
                    optCache[index] = {};
                }
                ['speciation', 'unit', 'method'].forEach(function(name) {
                    var defaults = chr['default_' + name + 's'];
                    if (!defaults || !defaults.length) {
                        return;
                    }
                    var $field = getField(index, name + '_id');
                    if (!optCache[index][name]) {
                        optCache[index][name] = $field.find('option');
                    }
                    var $groups = $field.find('optgroup');
                    var optById = {};
                    optCache[index][name].each(function(i, opt) {
                        optById[$(opt).val()] = opt;
                        $(opt).appendTo($groups[1]);
                    });
                    defaults.forEach(function(optId) {
                        if (optId === null) {
                            optId = '';
                        }
                        $(optById[optId]).appendTo($groups[0]);
                    });
                    $field.val(defaults[0]).selectmenu('refresh');
                });
            });
        }

        function setValue(index) {
            var $val = getField(index, 'value');
            var $qual = getField(index, 'qualifier');
            var val = $val.val();
            $qual.find('option').each(function(i, opt) {
                var optVal = $(opt).val();
                [optVal, optVal.toLowerCase()].forEach(function(ov) {
                    if (val.indexOf(ov) != -1) {
                        $qual.val(optVal).selectmenu('refresh');
                        $val.val(val.replace(ov, '').trim());
                    }
                });
            });
        }

        function lookupDomain(index, name) {
            var $field = getField(index, name);
            var tmpl = require('wq/template');
            var modelName = {
                'type_id': 'characteristic',
                'method_id': 'analyticalmethod',
                'unit_id': 'measureunit',
                'speciation_id': 'methodspeciation',
            }[name];
            if (!modelName) {
                return;
            }
            var url = '/' + modelName + 's/unused';
            $field.val('').selectmenu('refresh');
            require('wq/spinner').start();
            self.app.models[modelName].store.fetch(url).then(function(unused) {
                require('wq/spinner').stop();
                unused.title = name.replace('_id', '');
                var $popup = $(tmpl.render('domainselect', unused));
                $popup.appendTo($page);
                $popup.popup();
                $popup.trigger('create');
                $popup.popup('open');
                $popup.on('click', 'a[data-id]', function(evt) {
                    var $opt = $field.find('option[value=LOOKUP]');
                    var id = $(evt.currentTarget).data('id');
                    $opt.val(id).html(id);
                    $field.val(id).selectmenu('refresh');
                });
            });
        }

        function getField(index, name) {
            var query = '[name="results[' + index + '][' + name + ']"]';
            return $page.find(query);
        }
    }
})
