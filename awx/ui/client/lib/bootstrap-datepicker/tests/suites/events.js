module('Events', {
    setup: function(){
        this.input = $('<input type="text" value="31-03-2011">')
                        .appendTo('#qunit-fixture')
                        .datepicker({format: "dd-mm-yyyy"})
                        .focus(); // Activate for visibility checks
        this.dp = this.input.data('datepicker')
        this.picker = this.dp.picker;
    },
    teardown: function(){
        this.picker.remove();
    }
});

test('Selecting a year from decade view triggers changeYear', function(){
    var target,
        triggered = 0;

    this.input.on('changeYear', function(){
        triggered++;
    });

    equal(this.dp.viewMode, 0);
    target = this.picker.find('.datepicker-days thead th.datepicker-switch');
    ok(target.is(':visible'), 'View switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-months').is(':visible'), 'Month picker is visible');
    equal(this.dp.viewMode, 1);
    // Not modified when switching modes
    datesEqual(this.dp.viewDate, UTCDate(2011, 2, 31));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 31));

    target = this.picker.find('.datepicker-months thead th.datepicker-switch');
    ok(target.is(':visible'), 'View switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-years').is(':visible'), 'Year picker is visible');
    equal(this.dp.viewMode, 2);
    // Not modified when switching modes
    datesEqual(this.dp.viewDate, UTCDate(2011, 2, 31));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 31));

    // Change years to test internal state changes
    target = this.picker.find('.datepicker-years tbody span:contains(2010)');
    target.click();
    equal(this.dp.viewMode, 1);
    // Only viewDate modified
    datesEqual(this.dp.viewDate, UTCDate(2010, 2, 1));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 31));
    equal(triggered, 1);
});

test('Navigating forward/backward from month view triggers changeYear', function(){
    var target,
        triggered = 0;

    this.input.on('changeYear', function(){
        triggered++;
    });

    equal(this.dp.viewMode, 0);
    target = this.picker.find('.datepicker-days thead th.datepicker-switch');
    ok(target.is(':visible'), 'View switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-months').is(':visible'), 'Month picker is visible');
    equal(this.dp.viewMode, 1);

    target = this.picker.find('.datepicker-months thead th.prev');
    ok(target.is(':visible'), 'Prev switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-months').is(':visible'), 'Month picker is visible');
    equal(triggered, 1);

    target = this.picker.find('.datepicker-months thead th.next');
    ok(target.is(':visible'), 'Next switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-months').is(':visible'), 'Month picker is visible');
    equal(triggered, 2);
});

test('Selecting a month from year view triggers changeMonth', function(){
    var target,
        triggered = 0;

    this.input.on('changeMonth', function(){
        triggered++;
    });

    equal(this.dp.viewMode, 0);
    target = this.picker.find('.datepicker-days thead th.datepicker-switch');
    ok(target.is(':visible'), 'View switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-months').is(':visible'), 'Month picker is visible');
    equal(this.dp.viewMode, 1);
    // Not modified when switching modes
    datesEqual(this.dp.viewDate, UTCDate(2011, 2, 31));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 31));

    target = this.picker.find('.datepicker-months tbody span:contains(Apr)');
    target.click();
    equal(this.dp.viewMode, 0);
    // Only viewDate modified
    datesEqual(this.dp.viewDate, UTCDate(2011, 3, 1));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 31));
    equal(triggered, 1);
});

test('Navigating forward/backward from month view triggers changeMonth', function(){
    var target,
        triggered = 0;

    this.input.on('changeMonth', function(){
        triggered++;
    });

    equal(this.dp.viewMode, 0);
    target = this.picker.find('.datepicker-days thead th.prev');
    ok(target.is(':visible'), 'Prev switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-days').is(':visible'), 'Day picker is visible');
    equal(triggered, 1);

    target = this.picker.find('.datepicker-days thead th.next');
    ok(target.is(':visible'), 'Next switcher is visible');

    target.click();
    ok(this.picker.find('.datepicker-days').is(':visible'), 'Day picker is visible');
    equal(triggered, 2);
});

test('format() returns a formatted date string', function(){
    var target,
        error, out;

    this.input.on('changeDate', function(e){
        try{
            out = e.format();
        }
        catch(e){
            error = e;
        }
    });

    equal(this.dp.viewMode, 0);
    target = this.picker.find('.datepicker-days tbody td:nth(15)');
    target.click();

    datesEqual(this.dp.viewDate, UTCDate(2011, 2, 14));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 14));
    equal(error, undefined)
    equal(out, '14-03-2011');
});

test('format(altformat) returns a formatted date string', function(){
    var target,
        error, out;

    this.input.on('changeDate', function(e){
        try{
            out = e.format('m/d/yy');
        }
        catch(e){
            error = e;
        }
    });

    equal(this.dp.viewMode, 0);
    target = this.picker.find('.datepicker-days tbody td:nth(15)');
    target.click();

    datesEqual(this.dp.viewDate, UTCDate(2011, 2, 14));
    datesEqual(this.dp.dates[0], UTCDate(2011, 2, 14));
    equal(error, undefined)
    equal(out, '3/14/11');
});

test('format(ix) returns a formatted date string of the ix\'th date selected', function(){
    var target,
        error, out;

    this.dp._process_options({multidate: true});

    this.input.on('changeDate', function(e){
        try{
            out = e.format(2);
        }
        catch(e){
            error = e;
        }
    });

    target = this.picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '6'); // Mar 6
    target.click();

    target = this.picker.find('.datepicker-days tbody td:nth(15)');
    equal(target.text(), '14'); // Mar 16
    target.click();

    equal(this.dp.dates.length, 3);

    equal(error, undefined);
    equal(out, '14-03-2011');
});

test('format(ix, altformat) returns a formatted date string', function(){
    var target,
        error, out;

    this.dp._process_options({multidate: true});

    this.input.on('changeDate', function(e){
        try{
            out = e.format(2, 'm/d/yy');
        }
        catch(e){
            error = e;
        }
    });

    target = this.picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '6'); // Mar 6
    target.click();

    target = this.picker.find('.datepicker-days tbody td:nth(15)');
    equal(target.text(), '14'); // Mar 16
    target.click();

    equal(this.dp.dates.length, 3);

    equal(error, undefined);
    equal(out, '3/14/11');
});

test('Clear button: triggers change and changeDate events', function(){
    this.input = $('<input type="text" value="31-03-2011">')
                    .appendTo('#qunit-fixture')
                    .datepicker({
                        format: "dd-mm-yyyy",
                        clearBtn: true
                    })
                    .focus(); // Activate for visibility checks
    this.dp = this.input.data('datepicker');
    this.picker = this.dp.picker;

    var target,
        triggered_change = 0,
        triggered_changeDate = 0;

    this.input.on({
        changeDate: function(){
            triggered_changeDate++;
        },
        change: function(){
            triggered_change++;
        }
    });

    this.input.focus();
    ok(this.picker.find('.datepicker-days').is(':visible'), 'Days view visible');
    ok(this.picker.find('.datepicker-days tfoot .clear').is(':visible'), 'Clear button visible');

    target = this.picker.find('.datepicker-days tfoot .clear');
    target.click();

    equal(triggered_change, 1);
    equal(triggered_changeDate, 1);
});

test('setDate: triggers change and changeDate events', function(){
    this.input = $('<input type="text" value="31-03-2011">')
                    .appendTo('#qunit-fixture')
                    .datepicker({
                        format: "dd-mm-yyyy"
                    })
                    .focus(); // Activate for visibility checks
    this.dp = this.input.data('datepicker');
    this.picker = this.dp.picker;

    var target,
        triggered_change = 0,
        triggered_changeDate = 0;

    this.input.on({
        changeDate: function(){
            triggered_changeDate++;
        },
        change: function(){
            triggered_change++;
        }
    });

    this.input.focus();
    ok(this.picker.find('.datepicker-days').is(':visible'), 'Days view visible');

    this.dp.setDate(new Date(2011, 2, 5));

    equal(triggered_change, 2);
    equal(triggered_changeDate, 1);
});
