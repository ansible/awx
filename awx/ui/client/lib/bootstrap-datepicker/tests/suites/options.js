module('Options', {
    setup: function(){},
    teardown: function(){
        $('#qunit-fixture *').each(function(){
            var t = $(this);
            if ('datepicker' in t.data())
                t.datepicker('remove');
        });
    }
});

test('Autoclose', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    autoclose: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;


    input.focus();
    ok(picker.is(':visible'), 'Picker is visible');
    target = picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '4'); // Mar 4

    target.click();
    ok(picker.is(':not(:visible)'), 'Picker is hidden');
    datesEqual(dp.dates[0], UTCDate(2012, 2, 4));
    datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
});

test('Startview: year view (integer)', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    startView: 1
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':not(:visible)'), 'Days view hidden');
        ok(picker.find('.datepicker-months').is(':visible'), 'Months view visible');
        ok(picker.find('.datepicker-years').is(':not(:visible)'), 'Years view hidden');
});

test('Startview: year view (string)', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    startView: 'year'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':not(:visible)'), 'Days view hidden');
        ok(picker.find('.datepicker-months').is(':visible'), 'Months view visible');
        ok(picker.find('.datepicker-years').is(':not(:visible)'), 'Years view hidden');
});

test('Startview: decade view (integer)', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    startView: 2
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':not(:visible)'), 'Days view hidden');
        ok(picker.find('.datepicker-months').is(':not(:visible)'), 'Months view hidden');
        ok(picker.find('.datepicker-years').is(':visible'), 'Years view visible');
});

test('Startview: decade view (string)', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    startView: 'decade'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':not(:visible)'), 'Days view hidden');
        ok(picker.find('.datepicker-months').is(':not(:visible)'), 'Months view hidden');
        ok(picker.find('.datepicker-years').is(':visible'), 'Years view visible');
});

test('Today Button: today button not default', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .today').is(':not(:visible)'), 'Today button not visible');
});

test('Today Button: today visibility when enabled', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    todayBtn: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .today').is(':visible'), 'Today button visible');

        picker.find('.datepicker-days thead th.datepicker-switch').click();
        ok(picker.find('.datepicker-months').is(':visible'), 'Months view visible');
        ok(picker.find('.datepicker-months tfoot .today').is(':visible'), 'Today button visible');

        picker.find('.datepicker-months thead th.datepicker-switch').click();
        ok(picker.find('.datepicker-years').is(':visible'), 'Years view visible');
        ok(picker.find('.datepicker-years tfoot .today').is(':visible'), 'Today button visible');
});

test('Today Button: data-api', function(){
    var input = $('<input data-date-today-btn="true" />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .today').is(':visible'), 'Today button visible');
});

test('Today Button: moves to today\'s date', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    todayBtn: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .today').is(':visible'), 'Today button visible');

        target = picker.find('.datepicker-days tfoot .today');
        target.click();

        var d = new Date(),
            today = UTCDate(d.getFullYear(), d.getMonth(), d.getDate());
        datesEqual(dp.viewDate, today);
        datesEqual(dp.dates[0], UTCDate(2012, 2, 5));
});

test('Today Button: "linked" selects today\'s date', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    todayBtn: "linked"
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .today').is(':visible'), 'Today button visible');

        target = picker.find('.datepicker-days tfoot .today');
        target.click();

        var d = new Date(),
            today = UTCDate(d.getFullYear(), d.getMonth(), d.getDate());
        datesEqual(dp.viewDate, today);
        datesEqual(dp.dates[0], today);
});

test('Today Highlight: today\'s date is not highlighted by default', patch_date(function(Date){
    Date.now = UTCDate(2012, 2, 15);
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        equal(picker.find('.datepicker-days thead .datepicker-switch').text(), 'March 2012', 'Title is "March 2012"');

        target = picker.find('.datepicker-days tbody td:contains(15)');
        ok(!target.hasClass('today'), 'Today is not marked with "today" class');
        target = picker.find('.datepicker-days tbody td:contains(14)');
        ok(!target.hasClass('today'), 'Yesterday is not marked with "today" class');
        target = picker.find('.datepicker-days tbody td:contains(16)');
        ok(!target.hasClass('today'), 'Tomorrow is not marked with "today" class');
}));

test('Today Highlight: today\'s date is highlighted when not active', patch_date(function(Date){
    Date.now = new Date(2012, 2, 15);
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    todayHighlight: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        equal(picker.find('.datepicker-days thead .datepicker-switch').text(), 'March 2012', 'Title is "March 2012"');

        target = picker.find('.datepicker-days tbody td:contains(15)');
        ok(target.hasClass('today'), 'Today is marked with "today" class');
        target = picker.find('.datepicker-days tbody td:contains(14)');
        ok(!target.hasClass('today'), 'Yesterday is not marked with "today" class');
        target = picker.find('.datepicker-days tbody td:contains(16)');
        ok(!target.hasClass('today'), 'Tomorrow is not marked with "today" class');
}));

test('Clear Button: clear visibility when enabled', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    clearBtn: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .clear').is(':visible'), 'Clear button visible');

        picker.find('.datepicker-days thead th.datepicker-switch').click();
        ok(picker.find('.datepicker-months').is(':visible'), 'Months view visible');
        ok(picker.find('.datepicker-months tfoot .clear').is(':visible'), 'Clear button visible');

        picker.find('.datepicker-months thead th.datepicker-switch').click();
        ok(picker.find('.datepicker-years').is(':visible'), 'Years view visible');
        ok(picker.find('.datepicker-years tfoot .clear').is(':visible'), 'Clear button visible');
});

test('Clear Button: clears input value', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    clearBtn: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .clear').is(':visible'), 'Today button visible');

        target = picker.find('.datepicker-days tfoot .clear');
        target.click();

        equal(input.val(),'',"Input value has been cleared.")
        ok(picker.is(':visible'), 'Picker is visible');
});

test('Clear Button: hides datepicker if autoclose is on', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    clearBtn: true,
                    autoclose: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        input.focus();
        ok(picker.find('.datepicker-days').is(':visible'), 'Days view visible');
        ok(picker.find('.datepicker-days tfoot .clear').is(':visible'), 'Today button visible');

        target = picker.find('.datepicker-days tfoot .clear');
        target.click();

        equal(input.val(),'',"Input value has been cleared.");
        ok(picker.is(':not(:visible)'), 'Picker is hidden');

});

test('Active Toggle Default: when active date is selected it is not unset', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        // open our datepicker
        input.focus();

        // Initial value is selected
        ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 selected');

        // click on our active date
        target = picker.find('.datepicker-days .day.active');
        target.click();

        // make sure it's still set
        equal(input.val(), '2012-03-05', "Input value has not been cleared.");
});

test('Active Toggle Enabled (single date): when active date is selected it is unset', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    toggleActive: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        // open our datepicker
        input.focus();

        // Initial value is selected
        ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 selected');

        // click on our active date
        target = picker.find('.datepicker-days .day.active');
        target.click();

        // make sure it's no longer set
        equal(input.val(), '', "Input value has been cleared.");
});

test('Active Toggle Multidate Default: when one of the active dates is selected it is unset', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    multidate: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        // open our datepicker
        input.focus();

        // Initial value is selected
        ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 in dates');

        // Select additional date
        target = picker.find('.datepicker-days tbody td:nth(7)');
        target.click();
        datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 4), '2012-03-04 in dates');
        datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
        equal(input.val(), '2012-03-05,2012-03-04');

        // Unselect additional date
        target = picker.find('.datepicker-days tbody td:nth(7)');
        target.click();
        ok(dp.dates.contains(UTCDate(2012, 2, 4)) === -1, '2012-03-04 no longer in dates');
        datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
        equal(input.val(), '2012-03-05');
});

test('Active Toggle Disabled: when active date is selected it remains', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    toggleActive: false
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        // open our datepicker
        input.focus();

        // Initial value is selected
        ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 selected');

        // click on our active date
        target = picker.find('.datepicker-days .day.active');
        target.click();

        // make sure it's still set
        ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 still selected');
        datesEqual(dp.viewDate, UTCDate(2012, 2, 5));
        equal(input.val(), '2012-03-05');
});

test('Active Toggle Multidate Disabled: when activeToggle is set to false, but multidate is set, the option is ignored and selecting an active date it is unset', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    multidate: true,
                    toggleActive: false
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

        // open our datepicker
        input.focus();

        // Initial value is selected
        ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 in dates');

        // Select additional date
        target = picker.find('.datepicker-days tbody td:nth(7)');
        target.click();
        datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 4), '2012-03-04 in dates');
        datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
        equal(input.val(), '2012-03-05,2012-03-04');

        // Unselect additional date
        target = picker.find('.datepicker-days tbody td:nth(7)');
        target.click();
        ok(dp.dates.contains(UTCDate(2012, 2, 4)) === -1, '2012-03-04 no longer in dates');
        datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
        equal(input.val(), '2012-03-05');
});

test('DaysOfWeekDisabled', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    daysOfWeekDisabled: '1,5'
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;


    input.focus();
    target = picker.find('.datepicker-days tbody td:nth(22)');
    ok(target.hasClass('disabled'), 'Day of week is disabled');
    target = picker.find('.datepicker-days tbody td:nth(24)');
    ok(!target.hasClass('disabled'), 'Day of week is enabled');
    target = picker.find('.datepicker-days tbody td:nth(26)');
    ok(target.hasClass('disabled'), 'Day of week is disabled');
});


test('DatesDisabled', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    datesDisabled: ['2012-10-1', '2012-10-10', '2012-10-20']
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;


    input.focus();

    target = picker.find('.datepicker-days tbody td:nth(1)');
    ok(target.hasClass('disabled'), 'Day of week is disabled');
    ok(target.hasClass('disabled-date'), 'Date is disabled');
    target = picker.find('.datepicker-days tbody td:nth(2)');
    ok(!target.hasClass('disabled'), 'Day of week is enabled');
    target = picker.find('.datepicker-days tbody td:nth(10)');
    ok(target.hasClass('disabled'), 'Day of week is disabled');
    ok(target.hasClass('disabled-date'), 'Date is disabled');
    target = picker.find('.datepicker-days tbody td:nth(11)');
    ok(!target.hasClass('disabled'), 'Day of week is enabled');
    target = picker.find('.datepicker-days tbody td:nth(20)');
    ok(target.hasClass('disabled'), 'Day of week is disabled');
    ok(target.hasClass('disabled-date'), 'Date is disabled');
    target = picker.find('.datepicker-days tbody td:nth(21)');
    ok(!target.hasClass('disabled'), 'Day of week is enabled');
});

test('BeforeShowDay', function(){

    var beforeShowDay = function(date) {
        switch (date.getDate()){
            case 25:
                return {
                    tooltip: 'Example tooltip',
                    classes: 'active'
                };
            case 26:
                return "test26";
            case 27:
                return {enabled: false, classes:'test27'};
            case 28:
                return false;
        }
    };

    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    beforeShowDay: beforeShowDay
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();
    target = picker.find('.datepicker-days tbody td:nth(25)');
    equal(target.attr('title'), 'Example tooltip', '25th has tooltip');
    ok(!target.hasClass('disabled'), '25th is enabled');
    target = picker.find('.datepicker-days tbody td:nth(26)');
    ok(target.hasClass('test26'), '26th has test26 class');
    ok(!target.hasClass('disabled'), '26th is enabled');
    target = picker.find('.datepicker-days tbody td:nth(27)');
    ok(target.hasClass('test27'), '27th has test27 class');
    ok(target.hasClass('disabled'), '27th is disabled');
    target = picker.find('.datepicker-days tbody td:nth(28)');
    ok(target.hasClass('disabled'), '28th is disabled');
    target = picker.find('.datepicker-days tbody td:nth(29)');
    ok(!target.hasClass('disabled'), '29th is enabled');
});

test('Orientation: values are parsed correctly', function(){

    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd'
                }),
        dp = input.data('datepicker');

    equal(dp.o.orientation.x, 'auto');
    equal(dp.o.orientation.y, 'auto');

    dp._process_options({orientation: ''});
    equal(dp.o.orientation.x, 'auto', 'Empty value');
    equal(dp.o.orientation.y, 'auto', 'Empty value');

    dp._process_options({orientation: 'left'});
    equal(dp.o.orientation.x, 'left', '"left"');
    equal(dp.o.orientation.y, 'auto', '"left"');

    dp._process_options({orientation: 'right'});
    equal(dp.o.orientation.x, 'right', '"right"');
    equal(dp.o.orientation.y, 'auto', '"right"');

    dp._process_options({orientation: 'top'});
    equal(dp.o.orientation.x, 'auto', '"top"');
    equal(dp.o.orientation.y, 'top', '"top"');

    dp._process_options({orientation: 'bottom'});
    equal(dp.o.orientation.x, 'auto', '"bottom"');
    equal(dp.o.orientation.y, 'bottom', '"bottom"');

    dp._process_options({orientation: 'left top'});
    equal(dp.o.orientation.x, 'left', '"left top"');
    equal(dp.o.orientation.y, 'top', '"left top"');

    dp._process_options({orientation: 'left bottom'});
    equal(dp.o.orientation.x, 'left', '"left bottom"');
    equal(dp.o.orientation.y, 'bottom', '"left bottom"');

    dp._process_options({orientation: 'right top'});
    equal(dp.o.orientation.x, 'right', '"right top"');
    equal(dp.o.orientation.y, 'top', '"right top"');

    dp._process_options({orientation: 'right bottom'});
    equal(dp.o.orientation.x, 'right', '"right bottom"');
    equal(dp.o.orientation.y, 'bottom', '"right bottom"');

    dp._process_options({orientation: 'left right'});
    equal(dp.o.orientation.x, 'left', '"left right"');
    equal(dp.o.orientation.y, 'auto', '"left right"');

    dp._process_options({orientation: 'right left'});
    equal(dp.o.orientation.x, 'right', '"right left"');
    equal(dp.o.orientation.y, 'auto', '"right left"');

    dp._process_options({orientation: 'top bottom'});
    equal(dp.o.orientation.x, 'auto', '"top bottom"');
    equal(dp.o.orientation.y, 'top', '"top bottom"');

    dp._process_options({orientation: 'bottom top'});
    equal(dp.o.orientation.x, 'auto', '"bottom top"');
    equal(dp.o.orientation.y, 'bottom', '"bottom top"');

    dp._process_options({orientation: 'foo bar'});
    equal(dp.o.orientation.x, 'auto', '"foo bar"');
    equal(dp.o.orientation.y, 'auto', '"foo bar"');

    dp._process_options({orientation: 'foo left'});
    equal(dp.o.orientation.x, 'left', '"foo left"');
    equal(dp.o.orientation.y, 'auto', '"foo left"');

    dp._process_options({orientation: 'top bar'});
    equal(dp.o.orientation.x, 'auto', '"top bar"');
    equal(dp.o.orientation.y, 'top', '"top bar"');
});

test('startDate', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    startDate: new Date(2012, 9, 26)
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();
    target = picker.find('.datepicker-days tbody td:nth(25)');
    ok(target.hasClass('disabled'), 'Previous day is disabled');
    target = picker.find('.datepicker-days tbody td:nth(26)');
    ok(!target.hasClass('disabled'), 'Specified date is enabled');
    target = picker.find('.datepicker-days tbody td:nth(27)');
    ok(!target.hasClass('disabled'), 'Next day is enabled');
});

test('endDate', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    endDate: new Date(2012, 9, 26)
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();
    target = picker.find('.datepicker-days tbody td:nth(25)');
    ok(!target.hasClass('disabled'), 'Previous day is enabled');
    target = picker.find('.datepicker-days tbody td:nth(26)');
    ok(!target.hasClass('disabled'), 'Specified date is enabled');
    target = picker.find('.datepicker-days tbody td:nth(27)');
    ok(target.hasClass('disabled'), 'Next day is disabled');
});

test('Multidate', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    multidate: true
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();

    // Initial value is selected
    ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 (initial date) in dates');

    // Select first
    target = picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '4'); // Mar 4

    target.click();
    datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 4), '2012-03-04 in dates');
    datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
    equal(input.val(), '2012-03-05,2012-03-04');

    // Select second
    target = picker.find('.datepicker-days tbody td:nth(15)');
    equal(target.text(), '12'); // Mar 12

    target.click();
    datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 12), '2012-03-12 in dates');
    datesEqual(dp.viewDate, UTCDate(2012, 2, 12));
    equal(input.val(), '2012-03-05,2012-03-04,2012-03-12');

    // Deselect first
    target = picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '4'); // Mar 4

    target.click();
    ok(dp.dates.contains(UTCDate(2012, 2, 4)) === -1, '2012-03-04 no longer in dates');
    datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
    equal(input.val(), '2012-03-05,2012-03-12');
});

test('Multidate with limit', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    multidate: 2
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();

    // Initial value is selected
    ok(dp.dates.contains(UTCDate(2012, 2, 5)) !== -1, '2012-03-05 (initial date) in dates');

    // Select first
    target = picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '4'); // Mar 4

    target.click();
    datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 4), '2012-03-04 in dates');
    datesEqual(dp.viewDate, UTCDate(2012, 2, 4));
    equal(input.val(), '2012-03-05,2012-03-04');

    // Select second
    target = picker.find('.datepicker-days tbody td:nth(15)');
    equal(target.text(), '12'); // Mar 12

    target.click();
    datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 12), '2012-03-12 in dates');
    datesEqual(dp.viewDate, UTCDate(2012, 2, 12));
    equal(input.val(), '2012-03-04,2012-03-12');

    // Select third
    target = picker.find('.datepicker-days tbody td:nth(20)');
    equal(target.text(), '17'); // Mar 17

    target.click();
    datesEqual(dp.dates.get(-1), UTCDate(2012, 2, 17), '2012-03-17 in dates');
    ok(dp.dates.contains(UTCDate(2012, 2, 4)) === -1, '2012-03-04 no longer in dates');
    datesEqual(dp.viewDate, UTCDate(2012, 2, 17));
    equal(input.val(), '2012-03-12,2012-03-17');
});

test('Multidate Separator', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .val('2012-03-05')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    multidate: true,
                    multidateSeparator: ' '
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();

    // Select first
    target = picker.find('.datepicker-days tbody td:nth(7)');
    equal(target.text(), '4'); // Mar 4

    target.click();
    equal(input.val(), '2012-03-05 2012-03-04');

    // Select second
    target = picker.find('.datepicker-days tbody td:nth(15)');
    equal(target.text(), '12'); // Mar 12

    target.click();
    equal(input.val(), '2012-03-05 2012-03-04 2012-03-12');
});


test("Picker is shown on input focus when showOnFocus is not defined", function () {

    var input = $('<input />')
            .appendTo('#qunit-fixture')
            .val('2014-01-01')
            .datepicker({
            }),
        dp = input.data('datepicker'),
        picker = dp.picker;

    input.focus();

    ok(picker.is(":visible"), "Datepicker is visible");

});

test("Picker is shown on input focus when showOnFocus is true", function () {

    var input = $('<input />')
            .appendTo('#qunit-fixture')
            .val('2014-01-01')
            .datepicker({
                showOnFocus: true
            }),
        dp = input.data('datepicker'),
        picker = dp.picker;

    input.focus();

    ok(picker.is(":visible"), "Datepicker is visible");

});

test("Picker is hidden on input focus when showOnFocus is false", function () {

    var input = $('<input />')
            .appendTo('#qunit-fixture')
            .val('2014-01-01')
            .datepicker({
                showOnFocus: false
            }),
        dp = input.data('datepicker'),
        picker = dp.picker;

    input.focus();

    ok(picker.is(":hidden"), "Datepicker is hidden");

});

test('Container', function(){
    var testContainer = $('<div class="date-picker-container"/>')
            .appendTo('#qunit-fixture'),
        input = $('<input />')
            .appendTo('#qunit-fixture')
                .val('2012-10-26')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    container: '.date-picker-container',
                    startDate: new Date(2012, 9, 26)
                }),
        dp = input.data('datepicker'),
        target = dp.picker;
    input.focus();
    equal(target.parent()[0], testContainer[0], 'Container is not the testContainer that was specificed');
});

test('Default View Date', function(){
    var input = $('<input />')
                .appendTo('#qunit-fixture')
                .datepicker({
                    format: 'yyyy-mm-dd',
                    defaultViewDate: { year: 1977, month: 04, day: 25 }
                }),
        dp = input.data('datepicker'),
        picker = dp.picker,
        target;

    input.focus();

    equal(picker.find('.datepicker-days thead .datepicker-switch').text(), 'May 1977');
});

//datepicker-dropdown

test('Enable on readonly options (default)', function(){
    var input = $('<input readonly="readonly" />')
            .appendTo('#qunit-fixture')
            .datepicker({format: "dd-mm-yyyy"}),
        dp = input.data('datepicker'),
        picker = dp.picker;

    ok(!picker.is(':visible'));
    input.focus();
    ok(picker.is(':visible'));
});

test('Enable on readonly options (false)', function(){
    var input = $('<input readonly="readonly" />')
            .appendTo('#qunit-fixture')
            .datepicker({
                format: "dd-mm-yyyy",
                enableOnReadonly: false
            }),
        dp = input.data('datepicker'),
        picker = dp.picker;

    ok(!picker.is(':visible'));
    input.focus();
    ok(!picker.is(':visible'));
});
