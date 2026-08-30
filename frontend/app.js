let chartInstance = null;
let currentData = null;
let activeRegion = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

function initApp() {
    fetchDashboardData();
}

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.addEventListener('click', triggerDataRefresh);

    // Region tabs
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            activeRegion = e.target.getAttribute('data-region');
            renderDamCards();
        });
    });
}

function fetchDashboardData() {
    fetch('/api/lake-levels')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentData = data;
                updateUI();
            } else {
                console.error("Failed to load dashboard data:", data.error);
            }
        })
        .catch(err => console.error("Error fetching data:", err));
}

function triggerDataRefresh() {
    const refreshBtn = document.getElementById('refreshBtn');
    const spinner = document.getElementById('spinner');
    
    refreshBtn.classList.add('loading');
    spinner.classList.remove('hidden');

    fetch('/api/refresh', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentData = data;
                updateUI();
            } else {
                alert("Error synchronizing with MWRD: " + data.error);
            }
        })
        .catch(err => {
            console.error("Error syncing data:", err);
            alert("Connection error during sync.");
        })
        .finally(() => {
            refreshBtn.classList.remove('loading');
            spinner.classList.add('hidden');
        });
}

function updateUI() {
    if (!currentData || !currentData.current || !currentData.history) return;

    const latest = currentData.current;
    
    // Set report metadata
    const reportDateVal = latest.date;
    // Extract time from first dam that has it, or default
    const sampleDam = currentData.history[currentData.history.length - 1]?.dams?.[0];
    document.getElementById('reportDate').textContent = reportDateVal;
    document.getElementById('reportTime').textContent = sampleDam ? "08:00 AM" : "08:00 AM";

    // Calculate Summary stats for Pune & Mumbai
    calculateRegionalSummaries(latest.dams);
    
    // Render individual cards
    renderDamCards();

    // Render Trends Chart
    renderTrendsChart(currentData.history);
}

function calculateRegionalSummaries(dams) {
    // Designs:
    // Pune: Khadakwasla(55.91), Panshet(301.61), Warasgaon(363.13), Temghar(105.01), Pawana(274.32), Bhama Askhed(217.1) => Total 1317.08
    // Mumbai: Upper Vaitarna(331.31), Middle Vaitarna(193.53), Modak Sagar(174.79), Tansa(172.52), Bhatsa(942.1) => Total 1814.25

    let puneDesigned = 0;
    let puneLive = 0;
    let mumbaiDesigned = 0;
    let mumbaiLive = 0;

    dams.forEach(dam => {
        // Find designed live storage
        const designMap = {
            "Khadakwasla": 55.91,
            "Panshet": 301.61,
            "Warasgaon": 363.13,
            "Temghar": 105.01,
            "Pawana": 274.32,
            "Bhama Askhed": 217.10,
            "Upper Vaitarna": 331.31,
            "Middle Vaitarna": 193.53,
            "Modak Sagar": 174.79,
            "Tansa": 172.52,
            "Bhatsa": 942.10
        };
        const capacity = designMap[dam.name] || 100.0;

        if (dam.region === 'pune') {
            puneDesigned += capacity;
            puneLive += dam.live_storage_today;
        } else if (dam.region === 'mumbai') {
            mumbaiDesigned += capacity;
            mumbaiLive += dam.live_storage_today;
        }
    });

    const punePct = puneDesigned > 0 ? (puneLive / puneDesigned) * 100 : 0;
    const mumbaiPct = mumbaiDesigned > 0 ? (mumbaiLive / mumbaiDesigned) * 100 : 0;

    // Update Pune UI
    document.getElementById('puneTotalPct').textContent = `${punePct.toFixed(1)}%`;
    document.getElementById('puneTotalBar').style.width = `${Math.min(punePct, 100)}%`;
    document.getElementById('puneTotalVol').textContent = `${puneLive.toFixed(2)} / ${puneDesigned.toFixed(2)} Mcum`;

    // Update Mumbai UI
    document.getElementById('mumbaiTotalPct').textContent = `${mumbaiPct.toFixed(1)}%`;
    document.getElementById('mumbaiTotalBar').style.width = `${Math.min(mumbaiPct, 100)}%`;
    document.getElementById('mumbaiTotalVol').textContent = `${mumbaiLive.toFixed(2)} / ${mumbaiDesigned.toFixed(2)} Mcum`;
}

function renderDamCards() {
    const grid = document.getElementById('damsGrid');
    grid.innerHTML = '';

    if (!currentData || !currentData.current) return;
    const dams = currentData.current.dams;

    dams.forEach(dam => {
        // Filter by active region tab
        if (activeRegion !== 'all' && dam.region !== activeRegion) return;

        const designMap = {
            "Khadakwasla": 55.91,
            "Panshet": 301.61,
            "Warasgaon": 363.13,
            "Temghar": 105.01,
            "Pawana": 274.32,
            "Bhama Askhed": 217.10,
            "Upper Vaitarna": 331.31,
            "Middle Vaitarna": 193.53,
            "Modak Sagar": 174.79,
            "Tansa": 172.52,
            "Bhatsa": 942.10
        };
        const capacity = designMap[dam.name] || 100.0;

        const card = document.createElement('div');
        card.className = `dam-card glass ${dam.region}-dam`;
        
        card.innerHTML = `
            <div class="dam-card-header">
                <div class="dam-card-title">
                    <h3>${dam.name}</h3>
                    <span>${dam.region.toUpperCase()} REGION</span>
                </div>
                <div class="dam-card-pct">${dam.percentage_today.toFixed(1)}%</div>
            </div>
            
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${Math.min(dam.percentage_today, 100)}%"></div>
            </div>
            
            <div class="dam-stats">
                <div class="dam-stats-row">
                    <span class="dam-stats-label">Live Storage</span>
                    <span class="dam-stats-val">${dam.live_storage_today.toFixed(2)} Mcum</span>
                </div>
                <div class="dam-stats-row">
                    <span class="dam-stats-label">Designed Live Storage</span>
                    <span class="dam-stats-val">${capacity.toFixed(2)} Mcum</span>
                </div>
                <div class="dam-stats-row">
                    <span class="dam-stats-label">Last Year Same Day</span>
                    <span class="dam-stats-val" style="color: ${dam.percentage_last_year > dam.percentage_today ? '#ef4444' : '#10b981'}">
                        ${dam.percentage_last_year.toFixed(1)}%
                    </span>
                </div>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

function renderTrendsChart(history) {
    const ctx = document.getElementById('trendsChart').getContext('2d');
    
    // Process timeline labels (dates)
    const labels = history.map(h => h.date.split('/').slice(0, 2).join('/')); // DD/MM format
    
    // Compute averages for each date in history
    const puneData = [];
    const mumbaiData = [];

    const capacities = {
        "Khadakwasla": 55.91, "Panshet": 301.61, "Warasgaon": 363.13, "Temghar": 105.01, "Pawana": 274.32, "Bhama Askhed": 217.10,
        "Upper Vaitarna": 331.31, "Middle Vaitarna": 193.53, "Modak Sagar": 174.79, "Tansa": 172.52, "Bhatsa": 942.10
    };

    history.forEach(day => {
        let puneCapSum = 0;
        let puneLiveSum = 0;
        let mumCapSum = 0;
        let mumLiveSum = 0;

        day.dams.forEach(d => {
            const cap = capacities[d.name] || 100.0;
            if (d.region === 'pune') {
                puneCapSum += cap;
                puneLiveSum += d.live_storage_today;
            } else if (d.region === 'mumbai') {
                mumCapSum += cap;
                mumLiveSum += d.live_storage_today;
            }
        });

        const puneAvg = puneCapSum > 0 ? (puneLiveSum / puneCapSum) * 100 : 0;
        const mumAvg = mumCapSum > 0 ? (mumLiveSum / mumCapSum) * 100 : 0;

        puneData.push(puneAvg);
        mumbaiData.push(mumAvg);
    });

    if (chartInstance) {
        chartInstance.destroy();
    }

    // Chart.js config
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Pune Region (Average Capacity)',
                    data: puneData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    pointHoverRadius: 6
                },
                {
                    label: 'Mumbai Region (Average Capacity)',
                    data: mumbaiData,
                    borderColor: '#a855f7',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#0f172a',
                    titleColor: '#fff',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.dataset.label.split(' ')[0]} Region: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        borderColor: 'transparent'
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: { family: 'Outfit' }
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        borderColor: 'transparent'
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: { family: 'Outfit' },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}
