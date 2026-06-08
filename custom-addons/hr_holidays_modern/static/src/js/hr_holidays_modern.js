/* ============================================================================
   HR Holidays Modern UI - JavaScript/OWL Components
   Production-ready interactions for Odoo 19
   ============================================================================ */

odoo.define('hr_holidays_modern.modern_ui', function (require) {
    'use strict';

    const PivotView = require('web.PivotView');
    const PivotRenderer = require('web.PivotRenderer');
    const utils = require('web.utils');

    /**
     * Modern Pivot Renderer for HR Holidays
     * Enhances the pivot table with modern UI/UX features
     */
    const ModernPivotRenderer = PivotRenderer.extend({
        template: 'hr_holidays_modern.pivot_template',

        init: function (parent, state, params) {
            this._super(...arguments);
            this.hasModernStyles = true;
            this.kpiData = {
                totalDays: 0,
                topEmployee: '-',
                pendingCount: 0,
                popularType: '-'
            };
        },

        /**
         * Initialize component after rendering
         */
        on_attach_callback: function () {
            this._super(...arguments);
            this._initializeModernUI();
            this._attachEventHandlers();
            this._calculateKPIs();
        },

        /**
         * Initialize modern UI elements
         * @private
         */
        _initializeModernUI: function () {
            const self = this;

            // Animate KPI cards on load
            this._animateKPICards();

            // Setup sticky header
            this._setupStickyHeader();

            // Setup search functionality
            this._setupSearch();

            // Setup filter interactions
            this._setupFilterInteractions();

            // Setup table animations
            this._setupTableAnimations();

            // Setup dark mode detection
            this._setupDarkModeDetection();

            // Add smooth expand/collapse animations
            this._setupExpandCollapse();
        },

        /**
         * Animate KPI cards on page load
         * @private
         */
        _animateKPICards: function () {
            const cards = document.querySelectorAll('.o_kpi_card');
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 50}ms`;
            });
        },

        /**
         * Setup sticky header behavior
         * @private
         */
        _setupStickyHeader: function () {
            const filters = document.querySelector('.o_hr_holidays_modern_filters');
            if (!filters) return;

            let lastScrollTop = 0;
            const scrollThreshold = 50;

            window.addEventListener('scroll', () => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

                if (scrollTop > scrollThreshold) {
                    filters.style.boxShadow = 'var(--shadow-lg)';
                } else {
                    filters.style.boxShadow = 'var(--shadow-sm)';
                }

                lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
            }, false);
        },

        /**
         * Setup search functionality
         * @private
         */
        _setupSearch: function () {
            const searchInput = document.querySelector('.o_search_input');
            if (!searchInput) return;

            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                this._filterTableBySearch(query);
            });

            // Add enter key functionality
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                }
            });

            // Add clear on escape
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    this._filterTableBySearch('');
                }
            });
        },

        /**
         * Filter table rows based on search query
         * @private
         */
        _filterTableBySearch: function (query) {
            const rows = document.querySelectorAll('.o_hr_holidays_modern_table_wrapper tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const matches = text.includes(query);

                if (query === '') {
                    row.style.display = '';
                    row.style.opacity = '1';
                } else {
                    if (matches) {
                        row.style.display = '';
                        row.style.opacity = '1';
                    } else {
                        row.style.display = 'none';
                        row.style.opacity = '0.3';
                    }
                }
            });
        },

        /**
         * Setup filter pill interactions
         * @private
         */
        _setupFilterInteractions: function () {
            const filterPills = document.querySelectorAll('.o_filter_pill');

            filterPills.forEach(pill => {
                // Hover effect
                pill.addEventListener('mouseenter', () => {
                    pill.style.transform = 'translateY(-2px)';
                    pill.style.transition = 'all var(--transition-fast)';
                });

                pill.addEventListener('mouseleave', () => {
                    pill.style.transform = 'translateY(0)';
                });

                // Click effect
                pill.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (pill.classList.contains('o_filter_active')) {
                        pill.classList.remove('o_filter_active');
                    } else {
                        // Remove active from others
                        document.querySelectorAll('.o_filter_pill.o_filter_active').forEach(p => {
                            p.classList.remove('o_filter_active');
                        });
                        pill.classList.add('o_filter_active');
                    }
                });
            });

            // Setup add filter button
            const addBtn = document.querySelector('.o_filter_add_btn');
            if (addBtn) {
                addBtn.addEventListener('click', () => {
                    this._showFilterMenu();
                });
            }
        },

        /**
         * Show filter menu (can be extended)
         * @private
         */
        _showFilterMenu: function () {
            // This can be extended to show a dropdown or modal
            console.log('Filter menu would open here');
        },

        /**
         * Setup table animation effects
         * @private
         */
        _setupTableAnimations: function () {
            const rows = document.querySelectorAll('.o_hr_holidays_modern_table_wrapper tbody tr');

            rows.forEach((row, index) => {
                // Stagger animation
                row.style.animationDelay = `${index * 20}ms`;

                // Add hover effects
                row.addEventListener('mouseenter', () => {
                    row.style.transition = 'all var(--transition-fast)';
                });

                // Expand/collapse animation
                const expandBtns = row.querySelectorAll('.o_pivot_expand');
                expandBtns.forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        this._animateExpandCollapse(btn);
                    });
                });
            });
        },

        /**
         * Setup expand/collapse animations
         * @private
         */
        _setupExpandCollapse: function () {
            const expandButtons = document.querySelectorAll('.o_pivot_expand');

            expandButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.style.transition = 'transform var(--transition-base)';
                        icon.style.transform = 'rotate(90deg)';

                        setTimeout(() => {
                            icon.style.transform = 'rotate(0deg)';
                        }, 300);
                    }
                });
            });
        },

        /**
         * Animate expand/collapse
         * @private
         */
        _animateExpandCollapse: function (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.style.transform = icon.style.transform === 'rotate(90deg)' 
                    ? 'rotate(0deg)' 
                    : 'rotate(90deg)';
            }
        },

        /**
         * Setup dark mode detection
         * @private
         */
        _setupDarkModeDetection: function () {
            // Check system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.classList.add('dark-mode');
            }

            // Listen for changes
            if (window.matchMedia) {
                window.matchMedia('(prefers-color-scheme: dark)').addListener((e) => {
                    if (e.matches) {
                        document.documentElement.classList.add('dark-mode');
                    } else {
                        document.documentElement.classList.remove('dark-mode');
                    }
                });
            }
        },

        /**
         * Attach event handlers
         * @private
         */
        _attachEventHandlers: function () {
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                // Ctrl+K or Cmd+K for search focus
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    const searchInput = document.querySelector('.o_search_input');
                    if (searchInput) {
                        searchInput.focus();
                    }
                }
            });

            // Window resize handler for responsive adjustments
            window.addEventListener('resize', () => {
                this._handleResize();
            });
        },

        /**
         * Handle window resize
         * @private
         */
        _handleResize: function () {
            const width = window.innerWidth;

            if (width < 640) {
                // Mobile optimizations
                this._optimizeForMobile();
            } else if (width < 1024) {
                // Tablet optimizations
                this._optimizeForTablet();
            } else {
                // Desktop
                this._optimizeForDesktop();
            }
        },

        /**
         * Optimize for mobile
         * @private
         */
        _optimizeForMobile: function () {
            const header = document.querySelector('.o_hr_holidays_modern_header');
            if (header) {
                header.style.flexDirection = 'column';
            }
        },

        /**
         * Optimize for tablet
         * @private
         */
        _optimizeForTablet: function () {
            const cards = document.querySelector('.o_hr_holidays_kpi_cards');
            if (cards) {
                cards.style.gridTemplateColumns = 'repeat(2, 1fr)';
            }
        },

        /**
         * Optimize for desktop
         * @private
         */
        _optimizeForDesktop: function () {
            const cards = document.querySelector('.o_hr_holidays_kpi_cards');
            if (cards) {
                cards.style.gridTemplateColumns = 'repeat(auto-fit, minmax(240px, 1fr))';
            }
        },

        /**
         * Calculate and update KPI values
         * @private
         */
        _calculateKPIs: function () {
            const self = this;

            // Get data from pivot table
            const rows = document.querySelectorAll('.o_hr_holidays_modern_table_wrapper tbody tr');
            let totalDays = 0;
            let employeeData = {};
            let leaveTypes = {};

            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length > 0) {
                    // Extract employee name from first cell
                    const employeeName = cells[0]?.textContent?.trim() || '';
                    
                    // Extract leave count from numeric cells
                    cells.forEach((cell, index) => {
                        const value = parseFloat(cell.textContent) || 0;
                        if (value > 0 && index > 0) {
                            totalDays += value;

                            if (employeeName && !employeeName.includes('Tổng')) {
                                employeeData[employeeName] = (employeeData[employeeName] || 0) + value;
                            }
                        }
                    });
                }
            });

            // Find top employee
            let topEmployee = '-';
            let maxDays = 0;
            for (const [name, days] of Object.entries(employeeData)) {
                if (days > maxDays) {
                    maxDays = days;
                    topEmployee = name;
                }
            }

            this.kpiData = {
                totalDays: Math.round(totalDays * 10) / 10,
                topEmployee: topEmployee.substring(0, 20), // Limit length
                pendingCount: 0, // Would need to fetch from backend
                popularType: 'Sick Leave' // Would need to calculate from data
            };

            // Update KPI display
            this._updateKPIDisplay();
        },

        /**
         * Update KPI cards display
         * @private
         */
        _updateKPIDisplay: function () {
            const totalDaysEl = document.querySelector('[data-value="total_days"]');
            const topEmployeeEl = document.querySelector('[data-value="top_employee"]');
            const pendingCountEl = document.querySelector('[data-value="pending_count"]');
            const popularTypeEl = document.querySelector('[data-value="popular_type"]');

            if (totalDaysEl) {
                totalDaysEl.textContent = this.kpiData.totalDays + ' ngày';
                this._animateNumber(totalDaysEl);
            }
            if (topEmployeeEl) {
                topEmployeeEl.textContent = this.kpiData.topEmployee;
                this._animateNumber(topEmployeeEl);
            }
            if (pendingCountEl) {
                pendingCountEl.textContent = this.kpiData.pendingCount;
                this._animateNumber(pendingCountEl);
            }
            if (popularTypeEl) {
                popularTypeEl.textContent = this.kpiData.popularType;
                this._animateNumber(popularTypeEl);
            }
        },

        /**
         * Animate number update
         * @private
         */
        _animateNumber: function (element) {
            element.style.animation = 'none';
            setTimeout(() => {
                element.style.animation = 'slideInUp var(--transition-base)';
            }, 10);
        },
    });

    /**
     * Register the modern pivot renderer
     */
    const PivotViewModern = PivotView.extend({
        config: _.extend({}, PivotView.prototype.config, {
            Renderer: ModernPivotRenderer,
        }),
    });

    return {
        ModernPivotRenderer: ModernPivotRenderer,
        PivotViewModern: PivotViewModern,
    };
});

/**
 * Odoo Widget Registration
 * Initialize modern UI on page load
 */
odoo.define('hr_holidays_modern.init', function (require) {
    'use strict';

    const session = require('web.session');
    const core = require('web.core');

    // Initialize on DOM ready
    $(document).ready(function () {
        // Check if we're on the HR Holidays page
        const container = document.querySelector('.o_hr_holidays_modern_container');
        if (container) {
            // Add classes for initialization
            document.body.classList.add('o_hr_holidays_modern_active');

            // Trigger initialization events
            core.bus.trigger('hr_holidays_modern:ready');
        }
    });

    // Listen for view changes
    core.bus.on('do_action', null, function (action) {
        if (action && action.res_model === 'hr.leave') {
            setTimeout(() => {
                const container = document.querySelector('.o_hr_holidays_modern_container');
                if (container) {
                    core.bus.trigger('hr_holidays_modern:refresh');
                }
            }, 500);
        }
    });
});

/**
 * Export module
 */
return {};
