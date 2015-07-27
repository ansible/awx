module('Methods', {
    setup: function(){
        this.input = $('<input type="text" value="31-03-2011">')
                        .appendTo('#qunit-fixture')
                        .datepicker({format: "dd-mm-yyyy"});
        this.dp = this.input.data('datepicker')
    },
    teardown: function(){
        this.dp.remove();
    }
});

test('remove', function(){
    var returnedObject = this.dp.remove();
    // ...
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('show', function(){
    var returnedObject = this.dp.show();
    // ...
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('hide', function(){
    var returnedObject = this.dp.hide();
    // ...
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('update - String', function(){
    var returnedObject = this.dp.update('13-03-2012');
    datesEqual(this.dp.dates[0], UTCDate(2012, 2, 13));
    var date = this.dp.picker.find('.datepicker-days td:contains(13)');
    ok(date.is('.active'), 'Date is selected');
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('update - Date', function(){
    var returnedObject = this.dp.update(new Date(2012, 2, 13));
    datesEqual(this.dp.dates[0], UTCDate(2012, 2, 13));
    var date = this.dp.picker.find('.datepicker-days td:contains(13)');
    ok(date.is('.active'), 'Date is selected');
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('update - null', function(){
    var returnedObject = this.dp.update(null);
    equal(this.dp.dates[0], undefined);
    var selected = this.dp.picker.find('.datepicker-days td.active');
    equal(selected.length, 0, 'No date is selected');
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('setDate', function(){
    var date_in = new Date(2013, 1, 1),
        expected_date = new Date(Date.UTC(2013, 1, 1)),
        returnedObject;

    notEqual(this.dp.dates[0], date_in);
    returnedObject = this.dp.setDate(date_in);
    strictEqual(returnedObject, this.dp, "is chainable");
    datesEqual(this.dp.dates[0], expected_date);
});

test('setUTCDate', function(){
    var date_in = new Date(Date.UTC(2012, 3, 5)),
        expected_date = date_in,
        returnedObject;

    notEqual(this.dp.dates[0], date_in);
    returnedObject = this.dp.setUTCDate(date_in);
    strictEqual(returnedObject, this.dp, "is chainable");
    datesEqual(this.dp.dates[0], expected_date);
});

test('setStartDate', function(){
    var date_in = new Date(Date.UTC(2012, 3, 5)),
        expected_date = date_in,
        returnedObject = this.dp.setStartDate(date_in);
    // ...
    datesEqual(this.dp.o.startDate, expected_date);
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('setEndDate', function(){
    var date_in = new Date(Date.UTC(2012, 3, 5)),
        expected_date = date_in,
        returnedObject = this.dp.setEndDate(date_in);
    // ...
    datesEqual(this.dp.o.endDate, expected_date);
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('setDaysOfWeekDisabled - String', function(){
    var days_in = "0,6",
        expected_days = [0,6],
        returnedObject = this.dp.setDaysOfWeekDisabled(days_in);
    // ...
    deepEqual(this.dp.o.daysOfWeekDisabled, expected_days);
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('setDaysOfWeekDisabled - Array', function(){
    var days_in = [0,6],
        expected_days = days_in,
        returnedObject = this.dp.setDaysOfWeekDisabled(days_in);
    // ...
    deepEqual(this.dp.o.daysOfWeekDisabled, expected_days);
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('setValue', function(){
    var returnedObject = this.dp.setValue();
    // ...
    strictEqual(returnedObject, this.dp, "is chainable");
});

test('place', function(){
    var returnedObject = this.dp.place();
    // ...
    strictEqual(returnedObject, this.dp, "is chainable");
});
