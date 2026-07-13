# Config has no model file (data-only). Order matters: base models first,
# then inheriting overrides on hr.leave / hr.employee / hr.leave.allocation.
from . import hb_timeoff_policy_rule
from . import hb_leave_policy_log
from . import hb_leave_adjustment
from . import hb_work_day
from . import hocba_teaching_session
from . import hocba_leave_resolution
from . import hr_leave_teacher
from . import hr_leave_allocation
from . import hr_employee
from . import hr_leave_type
from . import hr_leave_emergency
from . import hr_leave_lapsed
from . import hr_leave_medical
from . import hr_leave_withdraw
from . import hb_timeoff_cron
from . import hb_timeoff_leave_analysis
from . import hb_timeoff_burnout_line
from . import hocba_attendance_policy
from . import hocba_attendance_leave
from . import hr_leave_attendance_sync
