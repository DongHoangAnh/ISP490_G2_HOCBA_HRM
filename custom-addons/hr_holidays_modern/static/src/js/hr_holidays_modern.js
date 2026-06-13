/** @odoo-module **/
/* ============================================================================
   HR Holidays Modern UI — Dashboard (Odoo 19 / OWL)
   Client action that loads real hr.leave data via ORM and renders KPI cards,
   leave-by-type breakdown, top employees and a pending-requests table.
   ============================================================================ */

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

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
            year: new Date().getFullYear(),
            kpi: { total: 0, pending: 0, approved: 0, approvedDays: 0, onLeaveToday: 0 },
            byType: [],
            topEmployees: [],
            pending: [],
        });
        onWillStart(() => this.load());
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

    // ---- data loading ------------------------------------------------------
    async load() {
        this.state.loading = true;

        const pad = (n) => String(n).padStart(2, "0");
        const d = new Date();
        const today = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

        const approvedYearDomain = [["state", "=", "validate"], ...this.yearDomain];

        const [
            total,
            pending,
            approved,
            approvedGrp,
            onLeaveToday,
            typeGroups,
            empGroups,
            pendingRecs,
        ] = await Promise.all([
            this.orm.searchCount("hr.leave", this.yearDomain),
            this.orm.searchCount("hr.leave", [["state", "in", PENDING_STATES]]),
            this.orm.searchCount("hr.leave", approvedYearDomain),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, [], ["number_of_days:sum"]),
            this.orm.searchCount("hr.leave", [
                ["state", "=", "validate"],
                ["date_from", "<=", `${today} 23:59:59`],
                ["date_to", ">=", `${today} 00:00:00`],
            ]),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, ["holiday_status_id"], ["number_of_days:sum", "__count"]),
            this.orm.formattedReadGroup("hr.leave", approvedYearDomain, ["employee_id"], ["number_of_days:sum", "__count"]),
            this.orm.searchRead(
                "hr.leave",
                [["state", "in", PENDING_STATES]],
                ["employee_id", "holiday_status_id", "date_from", "date_to", "number_of_days", "state"],
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
        this._open(`Đơn nghỉ năm ${this.state.year}`, this.yearDomain);
    }
    openPending() {
        this._open("Đơn chờ duyệt", [["state", "in", PENDING_STATES]]);
    }
    openApproved() {
        this._open(`Đơn đã duyệt ${this.state.year}`, [["state", "=", "validate"], ...this.yearDomain]);
    }
    openType(id, name) {
        this._open(`Nghỉ phép — ${name}`, [
            ["state", "=", "validate"],
            ["holiday_status_id", "=", id],
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
}

registry.category("actions").add("hr_holidays_modern_dashboard", HrHolidaysDashboard);
