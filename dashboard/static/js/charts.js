// Trading Bot Dashboard - Chart Management

let currentCandles = [];
let currentSignals = [];

/**
 * Display status message
 */
function showStatus(message, type = 'loading') {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            statusDiv.textContent = '';
            statusDiv.className = 'status';
        }, 3000);
    }
}

/**
 * Load and display candlestick chart
 */
async function loadChart() {
    const symbol = document.getElementById('symbol').value;
    const timeframe = document.getElementById('timeframe').value;
    
    showStatus(`Chargement des données ${symbol} (${timeframe})...`, 'loading');
    
    try {
        const response = await fetch(`/api/candles/${symbol}/${timeframe}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentCandles = await response.json();
        
        if (currentCandles.length === 0) {
            showStatus('Aucune donnée disponible. Utilisez scripts/ingest_candles.py pour récupérer des données.', 'error');
            return;
        }
        
        // Create candlestick trace
        const candleTrace = {
            x: currentCandles.map(c => c.timestamp),
            open: currentCandles.map(c => c.open),
            high: currentCandles.map(c => c.high),
            low: currentCandles.map(c => c.low),
            close: currentCandles.map(c => c.close),
            type: 'candlestick',
            name: symbol,
            increasing: { line: { color: '#26a69a' } },
            decreasing: { line: { color: '#ef5350' } }
        };
        
        // Create volume trace
        const volumeTrace = {
            x: currentCandles.map(c => c.timestamp),
            y: currentCandles.map(c => c.volume),
            type: 'bar',
            name: 'Volume',
            marker: { color: 'rgba(102, 126, 234, 0.3)' },
            yaxis: 'y2'
        };
        
        const layout = {
            title: `${symbol} - ${timeframe}`,
            xaxis: {
                title: 'Date',
                rangeslider: { visible: false }
            },
            yaxis: {
                title: 'Prix (USDT)',
                domain: [0.25, 1]
            },
            yaxis2: {
                title: 'Volume',
                domain: [0, 0.2]
            },
            showlegend: true,
            height: 600
        };
        
        Plotly.newPlot('chart', [candleTrace, volumeTrace], layout, {responsive: true});
        
        showStatus(`✅ ${currentCandles.length} bougies chargées avec succès`, 'success');
        
    } catch (error) {
        console.error('Error loading chart:', error);
        showStatus(`❌ Erreur lors du chargement: ${error.message}`, 'error');
    }
}

/**
 * Load and display trading signals
 */
async function loadSignals() {
    if (currentCandles.length === 0) {
        showStatus('Veuillez d\'abord charger les données du graphique', 'error');
        return;
    }
    
    const symbol = document.getElementById('symbol').value;
    const timeframe = document.getElementById('timeframe').value;
    
    showStatus('Génération des signaux de trading...', 'loading');
    
    try {
        const response = await fetch(`/api/signals/${symbol}/${timeframe}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentSignals = await response.json();
        
        if (currentSignals.length === 0) {
            showStatus('Aucun signal généré pour cette période', 'success');
            return;
        }
        
        // Separate buy and sell signals
        const buySignals = currentSignals.filter(s => s.type === 'buy');
        const sellSignals = currentSignals.filter(s => s.type === 'sell');
        
        // Create signal traces
        const buyTrace = {
            x: buySignals.map(s => s.timestamp),
            y: buySignals.map(s => s.price),
            mode: 'markers',
            type: 'scatter',
            name: 'Buy Signal',
            marker: {
                color: '#26a69a',
                size: 12,
                symbol: 'triangle-up'
            },
            text: buySignals.map(s => `BUY<br>Prix: ${s.price}<br>Conf: ${s.confidence}<br>${s.reason}`),
            hoverinfo: 'text'
        };
        
        const sellTrace = {
            x: sellSignals.map(s => s.timestamp),
            y: sellSignals.map(s => s.price),
            mode: 'markers',
            type: 'scatter',
            name: 'Sell Signal',
            marker: {
                color: '#ef5350',
                size: 12,
                symbol: 'triangle-down'
            },
            text: sellSignals.map(s => `SELL<br>Prix: ${s.price}<br>Conf: ${s.confidence}<br>${s.reason}`),
            hoverinfo: 'text'
        };
        
        // Add signals to existing chart
        Plotly.addTraces('chart', [buyTrace, sellTrace]);
        
        showStatus(`✅ ${currentSignals.length} signaux affichés (${buySignals.length} buy, ${sellSignals.length} sell)`, 'success');
        
    } catch (error) {
        console.error('Error loading signals:', error);
        showStatus(`❌ Erreur lors du chargement des signaux: ${error.message}`, 'error');
    }
}

/**
 * Run backtest and display results
 */
async function runBacktest() {
    const symbol = document.getElementById('symbol').value;
    const timeframe = document.getElementById('timeframe').value;
    
    showStatus('Exécution du backtest...', 'loading');
    
    try {
        const response = await fetch('/api/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                timeframe: timeframe,
                initial_cash: 10000,
                risk_per_trade: 0.02
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Display results
        const resultsDiv = document.getElementById('backtest-results');
        const contentDiv = document.getElementById('backtest-content');
        
        const pnlClass = result.pnl >= 0 ? 'positive' : 'negative';
        
        contentDiv.innerHTML = `
            <div class="metric">
                <div class="metric-label">Capital Initial</div>
                <div class="metric-value">${result.initial_cash.toFixed(2)} USDT</div>
            </div>
            <div class="metric">
                <div class="metric-label">Capital Final</div>
                <div class="metric-value">${result.final_equity.toFixed(2)} USDT</div>
            </div>
            <div class="metric">
                <div class="metric-label">PnL</div>
                <div class="metric-value ${pnlClass}">${result.pnl.toFixed(2)} USDT</div>
            </div>
            <div class="metric">
                <div class="metric-label">Rendement</div>
                <div class="metric-value ${pnlClass}">${result.pnl_pct.toFixed(2)}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Nombre de Trades</div>
                <div class="metric-value">${result.num_trades}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Trades Gagnants</div>
                <div class="metric-value positive">${result.winning_trades}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Trades Perdants</div>
                <div class="metric-value negative">${result.losing_trades}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">${result.win_rate.toFixed(2)}%</div>
            </div>
        `;
        
        resultsDiv.style.display = 'block';
        
        showStatus('✅ Backtest terminé avec succès', 'success');
        
    } catch (error) {
        console.error('Error running backtest:', error);
        showStatus(`❌ Erreur lors du backtest: ${error.message}`, 'error');
    }
}

// Auto-load chart on page load if data exists
window.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard loaded successfully');
});
