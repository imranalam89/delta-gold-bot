"""
Generates gold_dom_trap_backtest.html - an interactive, self-contained dashboard
visualizing the Gold Level-2 DOM Trap & Order Flow Absorption backtest.
"""

import os
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'trades_GOLD_DOM_TRAP_ABSORPTION.csv')
OUT_HTML = os.path.join(BASE_DIR, 'gold_dom_trap_backtest.html')

def build_dashboard():
    df = pd.read_csv(CSV_PATH)
    
    # Precompute metrics
    total_trades = len(df)
    wins = df[df['net_pnl'] > 0]
    losses = df[df['net_pnl'] <= 0]
    win_rate = (len(wins) / total_trades) * 100.0
    
    total_gross = df['gross_pnl'].sum()
    total_fees = df['total_fees'].sum()
    total_net = df['net_pnl'].sum()
    
    gross_win = wins['gross_pnl'].sum()
    gross_loss = abs(losses['gross_pnl'].sum())
    profit_factor = gross_win / gross_loss if gross_loss > 0 else 0.0
    
    # Cumulative equity
    cum_net = df['net_pnl'].cumsum().tolist()
    initial_cap = 100.0
    equity_curve = [initial_cap] + [initial_cap + x for x in cum_net]
    
    peaks = np.maximum.accumulate(equity_curve)
    drawdowns = [e - p for e, p in zip(equity_curve, peaks)]
    max_dd = min(drawdowns)
    max_dd_pct = min([(d / p) * 100 for d, p in zip(drawdowns, peaks)])
    
    # Monthly stats
    df['entry_dt'] = pd.to_datetime(df['entry_time'])
    df['month'] = df['entry_dt'].dt.strftime('%Y-%m')
    monthly_grp = df.groupby('month').agg(
        trades=('trade_id', 'count'),
        wins=('exit_reason', lambda x: (x == 'TAKE_PROFIT').sum()),
        gross=('gross_pnl', 'sum'),
        net=('net_pnl', 'sum'),
        fees=('total_fees', 'sum')
    ).reset_index()
    monthly_data = monthly_grp.to_dict(orient='records')

    # Convert trades to dict for JSON injection
    trades_json = df.to_dict(orient='records')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gold Level-2 DOM Trap & Order Flow Backtest Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg: #0b0e14;
            --card-bg: #151921;
            --card-border: #232936;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --accent-gold: #f59e0b;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
        }}
        body {{
            margin: 0;
            padding: 24px;
            background-color: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            color: var(--accent-gold);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge {{
            background: rgba(245, 158, 11, 0.15);
            color: var(--accent-gold);
            border: 1px solid var(--accent-gold);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }}
        .grid-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 16px;
        }}
        .stat-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .stat-val {{
            font-size: 22px;
            font-weight: 700;
        }}
        .green {{ color: var(--accent-green); }}
        .red {{ color: var(--accent-red); }}
        .gold {{ color: var(--accent-gold); }}
        .blue {{ color: var(--accent-blue); }}
        
        .charts-container {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        @media(max-width: 1024px) {{
            .charts-container {{ grid-template-columns: 1fr; }}
        }}
        .chart-box {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 20px;
        }}
        .chart-title {{
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text-main);
        }}
        
        .table-box {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 20px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}
        th {{
            color: var(--text-muted);
            padding: 10px 12px;
            border-bottom: 1px solid var(--card-border);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #1a202c;
        }}
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        .pill {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .pill-long {{ background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }}
        .pill-short {{ background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid var(--accent-red); }}
        .pill-tp {{ background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }}
        .pill-sl {{ background: rgba(239, 68, 68, 0.2); color: var(--accent-red); }}
        
        .rules-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
            line-height: 1.6;
        }}
        .rules-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 15px;
        }}
        @media(max-width: 768px) {{
            .rules-grid {{ grid-template-columns: 1fr; }}
        }}
        .rule-col h4 {{
            margin-top: 0;
            color: var(--accent-gold);
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 6px;
        }}
        ul {{
            margin: 0;
            padding-left: 20px;
            font-size: 13px;
            color: var(--text-muted);
        }}
        li {{ margin-bottom: 8px; }}
        li b {{ color: var(--text-main); }}
    </style>
</head>
<body>

    <div class="header">
        <div>
            <h1>🏆 Gold Level-2 DOM Trap & Order Flow Backtest</h1>
            <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
                Instrument: CME Gold Futures (GC) / 15-Minute Chart / Bar-by-Bar 1-Minute Path Verification
            </div>
        </div>
        <div class="badge">1:3.00 Fixed Risk-Reward (RR)</div>
    </div>

    <!-- Rule Specification Overview -->
    <div class="rules-card">
        <h3 style="margin-top:0; color:var(--text-main); font-size:16px;">Strategy Architecture & Institutional Defense Conditions</h3>
        <div class="rules-grid">
            <div class="rule-col">
                <h4>A. Long Entry Setup (Bear Trap Defense)</h4>
                <ul>
                    <li><b>The Sweep:</b> Previous 15m candle low swept below 24-bar swing low (<code>sr_low</code>).</li>
                    <li><b>The Reclaim:</b> Current 15m candle closes back above <code>sr_low</code> AND closes > previous close.</li>
                    <li><b>Rejection Wick:</b> Lower wick &ge; 25% of total range OR current close > previous open.</li>
                    <li><b>Delta Absorption Flip:</b> Delta flips negative to positive (<code>prevΔ &lt; 0 &rarr; currΔ &gt; 0</code>) OR delta &ge; 1.5% of volume.</li>
                    <li><b>Trend Alignment:</b> MTF consensus is <b>BULLISH</b> (1H/4H directional alignment).</li>
                    <li><b>Room-to-Run Filter:</b> Distance to 30m resistance (<code>sr_30_hi</code>) &ge; <b>1.5R</b> clearance.</li>
                </ul>
            </div>
            <div class="rule-col">
                <h4>B. Short Entry Setup (Bull Trap Absorption)</h4>
                <ul>
                    <li><b>The Sweep:</b> Previous 15m candle high swept above 24-bar swing high (<code>sr_high</code>).</li>
                    <li><b>The Reclaim:</b> Current 15m candle closes back below <code>sr_high</code> AND closes &lt; previous close.</li>
                    <li><b>Rejection Wick:</b> Upper wick &ge; 25% of total range OR current close &lt; previous open.</li>
                    <li><b>Delta Absorption Flip:</b> Delta flips positive to negative (<code>prevΔ &gt; 0 &rarr; currΔ &lt; 0</code>) OR negative delta &le; -1.5% of volume.</li>
                    <li><b>Trend Alignment:</b> MTF consensus is <b>BEARISH</b>.</li>
                    <li><b>Room-to-Run Filter:</b> Distance to 30m support (<code>sr_30_lo</code>) &ge; <b>1.5R</b> clearance.</li>
                </ul>
            </div>
        </div>
        <div style="margin-top: 15px; font-size: 13px; color: var(--text-muted); border-top: 1px solid var(--card-border); padding-top: 10px;">
            <b>Bracket & Sizing Math:</b> <code>sl_dist = max($2.50, trap_dist + $0.50)</code> | <code>Lots = max(1, round($5.00 / (sl_dist &times; 0.001)))</code> | Fixed Cash Risk: <b>$5.00</b> | Take Profit: <b>1:3.00 RR</b> | 15m Post-Trade Cooldown | 2-Hour Cascade Circuit Breaker on 2 consecutive SLs.
        </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid-stats">
        <div class="stat-card">
            <div class="stat-label">Net Profit ($100 Account)</div>
            <div class="stat-val green">+${total_net:.2f} <span style="font-size:14px;">(+{(total_net/initial_cap)*100:.1f}%)</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Profit Factor (Gross)</div>
            <div class="stat-val gold">{profit_factor:.2f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Win Rate (1:3 RR)</div>
            <div class="stat-val blue">{win_rate:.2f}% <span style="font-size:13px; color:var(--text-muted);">({len(wins)}W / {len(losses)}L)</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Trades</div>
            <div class="stat-val">{total_trades}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Gross PnL / Fees</div>
            <div class="stat-val" style="font-size:17px;"><span class="green">+${total_gross:.2f}</span> / <span class="red">-${total_fees:.2f}</span></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Max Drawdown</div>
            <div class="stat-val red">${abs(max_dd):.2f} <span style="font-size:13px;">({abs(max_dd_pct):.1f}%)</span></div>
        </div>
    </div>

    <!-- Charts -->
    <div class="charts-container">
        <div class="chart-box">
            <div class="chart-title">📈 Cumulative Net Equity Curve ($100 Starting Capital)</div>
            <canvas id="equityChart" height="110"></canvas>
        </div>
        <div class="chart-box">
            <div class="chart-title">📅 Monthly Net PnL Performance</div>
            <canvas id="monthlyChart" height="230"></canvas>
        </div>
    </div>

    <!-- Trade Journal Table -->
    <div class="table-box">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div class="chart-title" style="margin:0;">📝 Completed Trade Journal ({total_trades} Trades)</div>
            <div style="font-size:12px; color:var(--text-muted);">Delta Exchange 0.01% Taker Fee Deducted</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Entry Time (UTC)</th>
                    <th>Exit Time (UTC)</th>
                    <th>Side</th>
                    <th>Entry Px</th>
                    <th>Exit Px</th>
                    <th>SL Dist</th>
                    <th>Lots</th>
                    <th>Exit Reason</th>
                    <th>Duration</th>
                    <th>Net PnL ($)</th>
                    <th>R-Multiple</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''<tr>
                    <td>{t['trade_id']}</td>
                    <td>{t['entry_time']}</td>
                    <td>{t['exit_time']}</td>
                    <td><span class="pill {'pill-long' if t['direction'] == 'LONG' else 'pill-short'}">{t['direction']}</span></td>
                    <td>${t['entry_price']:.2f}</td>
                    <td>${t['exit_price']:.2f}</td>
                    <td>${t['sl_dist']:.2f}</td>
                    <td>{t['lots']:,}</td>
                    <td><span class="pill {'pill-tp' if t['exit_reason'] == 'TAKE_PROFIT' else 'pill-sl'}">{t['exit_reason']}</span></td>
                    <td>{t['duration_minutes']} min</td>
                    <td class="{'green' if t['net_pnl'] > 0 else 'red'}" style="font-weight:600;">{'+' if t['net_pnl'] > 0 else ''}${t['net_pnl']:.2f}</td>
                    <td class="{'green' if t['r_multiple'] > 0 else 'red'}">{'+' if t['r_multiple'] > 0 else ''}{t['r_multiple']:.2f}R</td>
                </tr>''' for t in trades_json])}
            </tbody>
        </table>
    </div>

    <script>
        // Equity Chart
        const eqData = {json.dumps(equity_curve)};
        const labels = Array.from({{length: eqData.length}}, (_, i) => i === 0 ? "Start" : `T#${{i}}`);

        const ctxEq = document.getElementById('equityChart').getContext('2d');
        new Chart(ctxEq, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Account Equity ($)',
                    data: eqData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    fill: true,
                    tension: 0.2,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: '#1a202c' }},
                        ticks: {{ color: '#64748b', maxTicksLimit: 15 }}
                    }},
                    y: {{
                        grid: {{ color: '#1a202c' }},
                        ticks: {{
                            color: '#64748b',
                            callback: value => '$' + value.toFixed(0)
                        }}
                    }}
                }}
            }}
        }});

        // Monthly Chart
        const mLabels = {json.dumps([m['month'] for m in monthly_data])};
        const mNet = {json.dumps([m['net'] for m in monthly_data])};
        const mColors = mNet.map(v => v >= 0 ? '#10b981' : '#ef4444');

        const ctxM = document.getElementById('monthlyChart').getContext('2d');
        new Chart(ctxM, {{
            type: 'bar',
            data: {{
                labels: mLabels,
                datasets: [{{
                    label: 'Net PnL ($)',
                    data: mNet,
                    backgroundColor: mColors,
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#94a3b8' }}
                    }},
                    y: {{
                        grid: {{ color: '#1a202c' }},
                        ticks: {{
                            color: '#64748b',
                            callback: value => '$' + value.toFixed(1)
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Interactive Dashboard generated successfully at: {OUT_HTML}")

if __name__ == '__main__':
    build_dashboard()
