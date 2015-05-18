export function searchDateRange(date) {
    return {
        from: moment(date).startOf('day'),
        to: moment(date).endOf('day')
    };
}
