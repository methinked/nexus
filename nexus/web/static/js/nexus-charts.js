/**
 * Nexus Charts - Centralized Chart.js configuration
 */

const NexusCharts = {
    // Theme Colors
    colors: {
        purple: { border: '#A855F7', bg: 'rgba(168, 85, 247, 0.1)' },
        blue: { border: '#3B82F6', bg: 'rgba(59, 130, 246, 0.1)' },
        green: { border: '#10B981', bg: 'rgba(16, 185, 129, 0.1)' },
        amber: { border: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)' },
        red: { border: '#EF4444', bg: 'rgba(239, 68, 68, 0.1)' },
        gray: { border: '#6B7280', bg: 'rgba(107, 114, 128, 0.1)' }
    },

    // Common Chart.js Options
    getCommonOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // Performance optimization for real-time data
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: false, // Cleaner look
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#9CA3AF',
                    bodyColor: '#F3F4F6',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(1);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute',
                        displayFormats: {
                            minute: 'HH:mm'
                        }
                    },
                    grid: {
                        display: false, // Cleaner look
                        color: '#374151'
                    },
                    ticks: {
                        color: '#9CA3AF',
                        font: {
                            family: '"JetBrains Mono", monospace',
                            size: 10
                        },
                        maxRotation: 0
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#374151',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9CA3AF',
                        font: {
                            family: '"JetBrains Mono", monospace',
                            size: 10
                        },
                        callback: function (value) {
                            return value.toFixed(0);
                        }
                    }
                }
            }
        };
    },

    /**
     * Create a simple Time Series chart
     * @param {CanvasRenderingContext2D} ctx 
     * @param {string} label Label for the dataset
     * @param {string} colorKey Key from NexusCharts.colors (e.g., 'purple')
     * @param {object} overrides Optional Chart.js overrides
     */
    createTimeSeriesChart(ctx, label, colorKey, overrides = {}) {
        const color = this.colors[colorKey] || this.colors.purple;
        const options = this.getCommonOptions();

        // Merge overrides deeply would be better, but simple assign is fine for now
        // Assuming simple scale overrides usually
        if (overrides.scales) {
            Object.assign(options.scales.y, overrides.scales.y || {});
        }

        // Add unit suffix to tooltip and y-axis if provided
        if (overrides.unit) {
            options.plugins.tooltip.callbacks.label = function (context) {
                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}${overrides.unit}`;
            };
            options.scales.y.ticks.callback = function (value) {
                return value + overrides.unit;
            };
        }

        return new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: label,
                    data: [], // Populated later
                    borderColor: color.border,
                    backgroundColor: color.bg,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4, // Smooth curves
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: options
        });
    },

    /**
     * Update a chart with new data
     * @param {Chart} chart Chart.js instance
     * @param {Array} metrics Array of metric objects
     * @param {string} valueKey Key to extract from metric (e.g., 'cpu_percent')
     */
    updateChartData(chart, metrics, valueKey) {
        if (!chart || !metrics) return;

        const times = metrics.map(m => new Date(m.timestamp));
        // Note: Data is usually passed reversed (newest first) from API? 
        // We need chronological for charts.
        // If metrics are [newest, ..., oldest], we need to reverse them here IF the API returns them that way.
        // Let's assume the caller handles order or we check timestamps. 
        // Standardizing: Charts expect Chronological (Oldest -> Newest).

        // Check if chronological
        let sortedMetrics = [...metrics];
        if (sortedMetrics.length > 1 && new Date(sortedMetrics[0].timestamp) > new Date(sortedMetrics[sortedMetrics.length - 1].timestamp)) {
            sortedMetrics.reverse();
        }

        const values = sortedMetrics.map(m => m[valueKey]);
        const labels = sortedMetrics.map(m => new Date(m.timestamp));

        // Update data
        // For simple single-dataset charts
        chart.data.labels = labels;
        chart.data.datasets[0].data = values.map((v, i) => ({ x: labels[i], y: v }));

        chart.update('none'); // 'none' mode for performance
    }
};
