# Config has no model file (data-only). Order matters: base models first,
# then inheriting overrides on hr.leave / hr.employee / hr.leave.allocation.
from . import hb_timeoff_policy_rule
from . import hb_leave_policy_log
from . import hb_leave_adjustment
from . import hb_leave_notification
from . import hb_work_day
from . import hr_leave_allocation
from . import hr_employee
from . import hr_leave_type
from . import hr_leave_emergency
from . import hr_leave_medical
from . import hr_leave_schedule_conflict
from . import hb_timeoff_cron
from . import hb_timeoff_leave_analysis
from . import hb_timeoff_burnout_line
