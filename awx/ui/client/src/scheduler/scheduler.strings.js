function SchedulerStrings (BaseString) {
    BaseString.call(this, 'scheduler');

    const { t } = this;
    const ns = this.scheduler;

    ns.state = {
        CREATE_SCHEDULE: t.s('CREATE SCHEDULE'),
        EDIT_SCHEDULE: t.s('EDIT SCHEDULE')
    };

    ns.list = {
        CLICK_TO_EDIT: t.s('Click to edit schedule.'),
        SCHEDULE_IS_ACTIVE: t.s('Schedule is active.'),
        SCHEDULE_IS_ACTIVE_CLICK_TO_STOP: t.s('Schedule is active. Click to stop.'),
        SCHEDULE_IS_STOPPED: t.s('Schedule is stopped.'),
        SCHEDULE_IS_STOPPED_CLICK_TO_STOP: t.s('Schedule is stopped. Click to activate.')
    }; 

    ns.form = {
        NAME: t.s('Name'),
        NAME_REQUIRED_MESSAGE: t.s('A schedule name is required.'),
        START_DATE: t.s('Start Date'),
        START_TIME: t.s('Start Time'),
        START_TIME_ERROR_MESSAGE: t.s('The time must be in HH24:MM:SS format.'),
        LOCAL_TIME_ZONE: t.s('Local Time Zone'),
        REPEAT_FREQUENCY: t.s('Repeat frequency'),
        FREQUENCY_DETAILS: t.s('Frequency Details'),
        EVERY: t.s('Every'),
        REPEAT_FREQUENCY_ERROR_MESSAGE: t.s('Please provide a value between 1 and 999.'),
        ON_DAY: t.s('on day'),
        MONTH_DAY_ERROR_MESSAGE: t.s('The day must be between 1 and 31.'),
        ON_THE: t.s('on the'),
        ON: t.s('on'),
        ON_DAYS: t.s('on days'),
        SUN: t.s('Sun'),
        MON: t.s('Mon'),
        TUE: t.s('Tue'),
        WED: t.s('Wed'),
        THU: t.s('Thu'),
        FRI: t.s('Fri'),
        SAT: t.s('Sat'),
        WEEK_DAY_ERROR_MESSAGE: t.s('Please select one or more days.'),
        END: t.s('End'),
        OCCURENCES: t.s('Occurrences'),
        END_DATE: t.s('End Date'),
        PROVIDE_VALID_DATE: t.s('Please provide a valid date.'),
        END_TIME: t.s('End Time'),
        SCHEDULER_OPTIONS_ARE_INVALID: t.s('The scheduler options are invalid, incomplete, or a date is in the past.'),
        SCHEDULE_DESCRIPTION: t.s('Schedule Description'),
        LIMITED_TO_FIRST_TEN: t.s('Limited to first 10'),
        DATE_FORMAT: t.s('Date format'),
        EXTRA_VARIABLES: t.s('Extra Variables'),
        PROMPT: t.s('Prompt'),
        CLOSE: t.s('Close'),
        CANCEL: t.s('Cancel'),
        SAVE: t.s('Save'),
        WARNING: t.s('Warning'),
        CREDENTIAL_REQUIRES_PASSWORD_WARNING: t.s('This Job Template has a default credential that requires a password before launch.  Adding or editing schedules is prohibited while this credential is selected.  To add or edit a schedule, credentials that require a password must be removed from the Job Template.'),
        SCHEDULE_NAME: t.s('Schedule name'),
        HH24: t.s('HH24'),
        MM: t.s('MM'),
        SS: t.s('SS'),
        DAYS_DATA: t.s('Days of data to keep')
    };

    ns.prompt = {
        CONFIRM: t.s('CONFIRM')
    };
}

SchedulerStrings.$inject = ['BaseStringService'];

export default SchedulerStrings;
