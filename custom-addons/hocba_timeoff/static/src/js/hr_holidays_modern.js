/** @odoo-module **/
/* ============================================================================
   HR Holidays Modern UI — Dashboard (Odoo 19 / OWL)
   Single client action that renders TWO different dashboards on the same screen
   depending on the current user's role:
     • Time Off Manager  → company-wide overview (KPI, by-type, top employees,
       pending queue).
     • Regular employee  → personal self-service view focused on the remaining
       leave balance per type, own requests and upcoming leaves.
   ============================================================================ */

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

const PENDING_STATES = ["confirm", "validate1"];

// Color palette used for the leave-type bars (cycled).
const PALETTE = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#06b6d4", "#ec4899", "#64748b"];

export class HrHolidaysDashboard extends Component {
    static template = "hr_holidays_modern.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            loading: true,
            isManager: false,
            year: new Date().getFullYear(),
            // ---- manager view ----
            kpi: { total: 0, pending: 0, approved: 0, approvedDays: 0, onLeaveToday: 0 },
            departments: [],
            selectedDept: false,
            byType: [],
            byDept: [],
            topEmployees: [],
            pending: [],
            // ---- employee view ----
            empMissing: false,
            empName: "",
            balances: [],
            totalRemaining: 0,
            empKpi: { pending: 0, approved: 0, approvedDays: 0 },
            myRequests: [],
            upcoming: [],
        });
        onWillStart(async () => {
            this.state.isManager = await user.hasGroup("hr_holidays.group_hr_holidays_manager");
            if (this.state.isManager) {
                this.state.departments = await this.orm.searchRead(
                    "hr.department", [], ["name"], { order: "name asc" }
                );
            }
            await this.refresh();
        });
    }

    get yearStart() {
        return `${this.state.year}-01-01 00:00:00`;
    }
    get yearEnd() {
        return `${this.state.year}-12-31 23:59:59`;
    }
    get yearDomain() {
        return [["date_from", ">=", this.yearStart], ["date_from", "<=", this.yearEnd]];
    }
    // Department filter applied across the whole manager dashboard (false = all).
    get deptDomain() {
        return this.state.selectedDept ? [["department_id", "=", this.state.selectedDept]] : [];
    }

    onDeptChange(ev) {
        const val = ev.target.value;
        this.state.selectedDept = val ? parseInt(val, 10) : false;
        this.load();
    }

    refresh() {
        return this.state.isManager ? this.load() : this.loadEmployee();
    }

    _today() {
        const pad = (n) => String(n).padStart(2, "0");
        const d = new Date();
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    }

    // ---- manager data loading ---------------------------------------------
    async load() {
        this.state.loading = true;

        const today = this._today();
        const dept = this.deptDomain;
        const approvedYearDomain = [["state", "=", "validate"], ...this.yearDomain, ...dept];
        const pendingDomain = [["state", "in", PENDING_STATES], ...dept];

        const [
            total,
            pending,
            approved,
            approvedGrp,
            onLeaveToday,
            typeGroups,
            deptGroups,
            empGroups,
            pendingRecs,
        ] = await Promise.all([
            this.orm.searchCount("hr.leave", [...this.yearDomain, ...dept]),
            this.orm.searchCount("hr.leave", pendingDomain),
            this.orm.searchCount("hr.leave", approvedYearDomain),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, [], ["number_of_days:sum"]),
            this.orm.searchCount("hr.leave", [
                ["state", "=", "validate"],
                ["date_from", "<=", `${today} 23:59:59`],
                ["date_to", ">=", `${today} 00:00:00`],
                ...dept,
            ]),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, ["holiday_status_id"], ["number_of_days:sum", "__count"]),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, ["department_id"], ["number_of_days:sum", "__count"]),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, ["employee_id"], ["number_of_days:sum", "__count"]),
            this.orm.searchRead(
                "hr.leave",
                pendingDomain,
                ["employee_id", "department_id", "holiday_status_id", "date_from", "date_to", "number_of_days", "state"],
                { limit: 8, order: "create_date desc" }
            ),
        ]);

        this.state.kpi = {
            total,
            pending,
            approved,
            approvedDays: (approvedGrp[0] && approvedGrp[0]["number_of_days:sum"]) || 0,
            onLeaveToday,
        };

        // Leave by type
        const types = typeGroups
            .map((g) => ({
                id: g.holiday_status_id ? g.holiday_status_id[0] : false,
                name: g.holiday_status_id ? g.holiday_status_id[1] : "Không xác định",
                days: g["number_of_days:sum"] || 0,
                count: g["__count"] || 0,
            }))
            .filter((t) => t.days > 0)
            .sort((a, b) => b.days - a.days);
        const maxTypeDays = Math.max(1, ...types.map((t) => t.days));
        types.forEach((t, i) => {
            t.pct = Math.round((t.days / maxTypeDays) * 100);
            t.color = PALETTE[i % PALETTE.length];
        });
        this.state.byType = types;

        // Leave by department
        const depts = deptGroups
            .map((g, i) => ({
                id: g.department_id ? g.department_id[0] : false,
                name: g.department_id ? g.department_id[1] : "Chưa có phòng ban",
                days: g["number_of_days:sum"] || 0,
                count: g["__count"] || 0,
                color: PALETTE[i % PALETTE.length],
            }))
            .filter((d) => d.days > 0)
            .sort((a, b) => b.days - a.days);
        const maxDeptDays = Math.max(1, ...depts.map((d) => d.days));
        depts.forEach((d) => (d.pct = Math.round((d.days / maxDeptDays) * 100)));
        this.state.byDept = depts;

        // Top employees
        const emps = empGroups
            .map((g) => ({
                id: g.employee_id ? g.employee_id[0] : false,
                name: g.employee_id ? g.employee_id[1] : "Không xác định",
                days: g["number_of_days:sum"] || 0,
                count: g["__count"] || 0,
            }))
            .filter((e) => e.days > 0)
            .sort((a, b) => b.days - a.days)
            .slice(0, 5);
        const maxEmpDays = Math.max(1, ...emps.map((e) => e.days));
        emps.forEach((e) => (e.pct = Math.round((e.days / maxEmpDays) * 100)));
        this.state.topEmployees = emps;

        // Pending requests
        this.state.pending = pendingRecs.map((r) => ({
            id: r.id,
            employee: r.employee_id ? r.employee_id[1] : "—",
            department: r.department_id ? r.department_id[1] : "—",
            type: r.holiday_status_id ? r.holiday_status_id[1] : "—",
            from: this.fmtDate(r.date_from),
            to: this.fmtDate(r.date_to),
            days: r.number_of_days || 0,
        }));

        this.state.loading = false;
    }

    // ---- employee (self-service) data loading -----------------------------
    async loadEmployee() {
        this.state.loading = true;
        this.state.empMissing = false;

        const emps = await this.orm.searchRead(
            "hr.employee",
            [["user_id", "=", user.userId]],
            ["id", "name"],
            { limit: 1 }
        );
        if (!emps.length) {
            this.empId = false;
            this.state.empMissing = true;
            this.state.loading = false;
            return;
        }
        const emp = emps[0];
        this.empId = emp.id;
        this.state.empName = emp.name;

        const today = this._today();
        const empDomain = [["employee_id", "=", emp.id]];
        const approvedYear = [...empDomain, ["state", "=", "validate"], ...this.yearDomain];

        const [types, pendingCnt, approvedCnt, approvedGrp, myReqs, upcoming] = await Promise.all([
            // Balance per leave type — computed for THIS employee via context.
            this.orm.searchRead(
                "hr.leave.type",
                [["requires_allocation", "=", true]],
                ["name", "max_leaves", "leaves_taken", "virtual_remaining_leaves"],
                { context: { employee_id: emp.id } }
            ),
            this.orm.searchCount("hr.leave", [...empDomain, ["state", "in", PENDING_STATES]]),
            this.orm.searchCount("hr.leave", approvedYear),
            this.orm.formattedReadGroup("hr.leave", approvedYear, [], ["number_of_days:sum"]),
            this.orm.searchRead(
                "hr.leave",
                empDomain,
                ["holiday_status_id", "date_from", "date_to", "number_of_days", "state"],
                { limit: 8, order: "create_date desc" }
            ),
            this.orm.searchRead(
                "hr.leave",
                [...empDomain, ["state", "=", "validate"], ["date_to", ">=", `${today} 00:00:00`]],
                ["holiday_status_id", "date_from", "date_to", "number_of_days"],
                { limit: 5, order: "date_from asc" }
            ),
        ]);

        // Leave balances — keep only types the employee actually has activity on.
        const bals = types
            .map((t, i) => ({
                id: t.id,
                name: t.name,
                allocated: t.max_leaves || 0,
                taken: t.leaves_taken || 0,
                remaining: t.virtual_remaining_leaves || 0,
                color: PALETTE[i % PALETTE.length],
            }))
            .filter((b) => b.allocated > 0 || b.taken > 0 || b.remaining !== 0);
        bals.forEach((b) => {
            b.pct = b.allocated > 0 ? Math.min(100, Math.round((b.taken / b.allocated) * 100)) : 0;
            b.low = b.allocated > 0 && b.remaining <= 2;
        });
        this.state.balances = bals;
        this.state.totalRemaining = bals.reduce((s, b) => s + (b.remaining || 0), 0);

        this.state.empKpi = {
            pending: pendingCnt,
            approved: approvedCnt,
            approvedDays: (approvedGrp[0] && approvedGrp[0]["number_of_days:sum"]) || 0,
        };

        this.state.myRequests = myReqs.map((r) => ({
            id: r.id,
            type: r.holiday_status_id ? r.holiday_status_id[1] : "—",
            from: this.fmtDate(r.date_from),
            to: this.fmtDate(r.date_to),
            days: r.number_of_days || 0,
            ...this.stateBadge(r.state),
        }));

        this.state.upcoming = upcoming.map((r) => ({
            id: r.id,
            type: r.holiday_status_id ? r.holiday_status_id[1] : "—",
            from: this.fmtDate(r.date_from),
            to: this.fmtDate(r.date_to),
            days: r.number_of_days || 0,
        }));

        this.state.loading = false;
    }

    // ---- helpers -----------------------------------------------------------
    fmtDate(val) {
        if (!val) {
            return "—";
        }
        // server datetime "YYYY-MM-DD HH:mm:ss" → "DD/MM/YYYY"
        const s = String(val).slice(0, 10);
        const [y, m, day] = s.split("-");
        return day && m && y ? `${day}/${m}/${y}` : s;
    }

    fmtDays(n) {
        return (Math.round((n || 0) * 10) / 10).toLocaleString("vi-VN");
    }

    stateBadge(s) {
        const map = {
            draft: { stateLabel: "Nháp", stateCls: "o_hhm_st--draft" },
            confirm: { stateLabel: "Chờ duyệt", stateCls: "o_hhm_st--pending" },
            validate1: { stateLabel: "Duyệt 1 phần", stateCls: "o_hhm_st--pending" },
            validate: { stateLabel: "Đã duyệt", stateCls: "o_hhm_st--ok" },
            refuse: { stateLabel: "Từ chối", stateCls: "o_hhm_st--refuse" },
        };
        return map[s] || { stateLabel: s, stateCls: "o_hhm_st--draft" };
    }

    // ---- drill-down --------------------------------------------------------
    _open(name, domain) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "hr.leave",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain,
            target: "current",
        });
    }
    openYear() {
        this._open(`Đơn nghỉ năm ${this.state.year}`, [...this.yearDomain, ...this.deptDomain]);
    }
    openPending() {
        this._open("Đơn chờ duyệt", [["state", "in", PENDING_STATES], ...this.deptDomain]);
    }
    openApproved() {
        this._open(`Đơn đã duyệt ${this.state.year}`, [["state", "=", "validate"], ...this.yearDomain, ...this.deptDomain]);
    }
    openType(id, name) {
        this._open(`Nghỉ phép — ${name}`, [
            ["state", "=", "validate"],
            ["holiday_status_id", "=", id],
            ...this.yearDomain,
        ]);
    }
    openDept(id, name) {
        this._open(`Nghỉ phép — ${name}`, [
            ["state", "=", "validate"],
            ["department_id", "=", id],
            ...this.yearDomain,
        ]);
    }
    openLeave(id) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "hr.leave",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ---- employee actions --------------------------------------------------
    openMyLeaves() {
        this._open("Nghỉ phép của tôi", [["employee_id", "=", this.empId]]);
    }
    openMyPending() {
        this._open("Đơn chờ duyệt của tôi", [
            ["employee_id", "=", this.empId],
            ["state", "in", PENDING_STATES],
        ]);
    }
    openNewRequest() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Tạo đơn nghỉ",
            res_model: "hr.leave",
            views: [[false, "form"]],
            target: "current",
            context: this.empId ? { default_employee_id: this.empId } : {},
        });
    }
}

registry.category("actions").add("hr_holidays_modern_dashboard", HrHolidaysDashboard);
