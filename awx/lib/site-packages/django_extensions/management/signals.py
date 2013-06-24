"""
signals we use to trigger regular batch jobs
"""
from django.dispatch import Signal

run_minutely_jobs = Signal()
run_quarter_hourly_jobs = Signal()
run_hourly_jobs = Signal()
run_daily_jobs = Signal()
run_weekly_jobs = Signal()
run_monthly_jobs = Signal()
run_yearly_jobs = Signal()
