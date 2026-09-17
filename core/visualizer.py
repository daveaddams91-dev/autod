"""Interactive HTML5/Canvas Visualizer Generator for Auto'd.

Synthesizes responsive, zero-dependency interactive browser demonstrations
deployed directly to GitHub Pages (https://Raj123-0.github.io/<repo-name>).
"""

from typing import Any, Dict


class VisualizerGenerator:
    """Generates interactive browser simulations for each technical domain."""

    @classmethod
    def generate_demo(cls, blueprint: Dict[str, Any]) -> str:
        """Generate a complete standalone HTML5 application tailored to the project domain."""
        domain_id = blueprint.get("domain", "computational_math")
        repo_name = blueprint.get("repo_name", "project")
        tagline = blueprint.get("tagline", "Interactive Simulation Demo")

        if domain_id == "aerospace_orbital":
            return cls._generate_orbital_demo(repo_name, tagline)
        elif domain_id == "numerical_physics":
            return cls._generate_physics_demo(repo_name, tagline)
        elif domain_id == "crypto_algorithms":
            return cls._generate_crypto_demo(repo_name, tagline)
        elif domain_id == "systems_compilers":
            return cls._generate_systems_demo(repo_name, tagline)
        else:
            return cls._generate_math_demo(repo_name, tagline)

    @staticmethod
    def _generate_orbital_demo(repo_name: str, tagline: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{repo_name} - Real-Time Orbit Simulation</title>
  <style>
    body {{ margin: 0; background: #0b0f19; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; flex-direction: column; height: 100vh; }}
    header {{ padding: 12px 24px; background: #151d2f; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; }}
    h1 {{ margin: 0; font-size: 1.1rem; color: #38bdf8; }}
    p.tagline {{ margin: 0; font-size: 0.85rem; color: #94a3b8; }}
    #container {{ display: flex; flex: 1; overflow: hidden; }}
    #canvas-container {{ flex: 1; position: relative; background: radial-gradient(circle at center, #111827 0%, #030712 100%); }}
    canvas {{ width: 100%; height: 100%; display: block; }}
    #sidebar {{ width: 320px; background: #111827; border-left: 1px solid #1e293b; padding: 20px; box-sizing: border-box; overflow-y: auto; }}
    .control-group {{ margin-bottom: 16px; }}
    label {{ display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em; }}
    input[type=range] {{ width: 100%; accent-color: #38bdf8; }}
    .val-display {{ float: right; color: #38bdf8; font-weight: bold; }}
    .stats-card {{ background: #1e293b; border-radius: 8px; padding: 12px; margin-top: 16px; font-size: 0.85rem; line-height: 1.5; }}
    a.gh-btn {{ color: #38bdf8; text-decoration: none; border: 1px solid #38bdf8; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; }}
    a.gh-btn:hover {{ background: rgba(56, 189, 248, 0.15); }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>🚀 {repo_name}</h1>
      <p class="tagline">{tagline}</p>
    </div>
    <a class="gh-btn" href="https://github.com/Raj123-0/{repo_name}" target="_blank">View on GitHub</a>
  </header>
  <div id="container">
    <div id="canvas-container">
      <canvas id="orbitCanvas"></canvas>
    </div>
    <div id="sidebar">
      <div class="control-group">
        <label>Semi-Major Axis (a) <span class="val-display" id="a-val">7,000 km</span></label>
        <input type="range" id="a-slider" min="6600" max="15000" value="7000" step="100">
      </div>
      <div class="control-group">
        <label>Eccentricity (e) <span class="val-display" id="e-val">0.15</span></label>
        <input type="range" id="e-slider" min="0" max="0.75" value="0.15" step="0.01">
      </div>
      <div class="control-group">
        <label>Time Warp <span class="val-display" id="warp-val">10x</span></label>
        <input type="range" id="warp-slider" min="1" max="50" value="10">
      </div>
      <div class="stats-card">
        <div><strong>Orbital Period:</strong> <span id="stat-period">96.2 min</span></div>
        <div><strong>Periapsis Alt:</strong> <span id="stat-peri">580 km</span></div>
        <div><strong>Apoapsis Alt:</strong> <span id="stat-apo">1,680 km</span></div>
        <div><strong>Orbital Speed:</strong> <span id="stat-vel">7.62 km/s</span></div>
      </div>
    </div>
  </div>
  <script>
    const canvas = document.getElementById('orbitCanvas');
    const ctx = canvas.getContext('2d');
    let a = 7000, e = 0.15, warp = 10, trueAnomaly = 0;
    const MU = 398600.4418, R_EARTH = 6378.137;

    function resize() {{
      canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
      canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    }}
    window.addEventListener('resize', resize);
    resize();

    document.getElementById('a-slider').oninput = e => {{ a = +e.target.value; document.getElementById('a-val').innerText = a.toLocaleString() + ' km'; }};
    document.getElementById('e-slider').oninput = ev => {{ e = +ev.target.value; document.getElementById('e-val').innerText = e.toFixed(2); }};
    document.getElementById('warp-slider').oninput = ev => {{ warp = +ev.target.value; document.getElementById('warp-val').innerText = warp + 'x'; }};

    function draw() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2, cy = canvas.height / 2;
      const scale = Math.min(canvas.width, canvas.height) / (2.6 * a);

      // Draw Earth
      ctx.beginPath();
      ctx.arc(cx, cy, R_EARTH * scale, 0, Math.PI * 2);
      ctx.fillStyle = '#0284c7';
      ctx.fill();
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw Orbit Path
      ctx.beginPath();
      const p = a * (1 - e * e);
      for (let th = 0; th <= Math.PI * 2; th += 0.02) {{
        const r = p / (1 + e * Math.cos(th));
        const x = cx + r * Math.cos(th) * scale;
        const y = cy - r * Math.sin(th) * scale;
        if (th === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }}
      ctx.closePath();
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Propagate Satellite
      const r_sat = p / (1 + e * Math.cos(trueAnomaly));
      const sat_x = cx + r_sat * Math.cos(trueAnomaly) * scale;
      const sat_y = cy - r_sat * Math.sin(trueAnomaly) * scale;

      ctx.beginPath();
      ctx.arc(sat_x, sat_y, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#f43f5e';
      ctx.fill();

      // Keplerian speed v = sqrt(MU * (2/r - 1/a))
      const v = Math.sqrt(MU * (2 / r_sat - 1 / a));
      const dTheta = (v / r_sat) * (warp * 0.05);
      trueAnomaly = (trueAnomaly + dTheta) % (Math.PI * 2);

      // Update metrics
      const periodSec = 2 * Math.PI * Math.sqrt(Math.pow(a, 3) / MU);
      document.getElementById('stat-period').innerText = (periodSec / 60).toFixed(1) + ' min';
      document.getElementById('stat-peri').innerText = Math.round(a * (1 - e) - R_EARTH).toLocaleString() + ' km';
      document.getElementById('stat-apo').innerText = Math.round(a * (1 + e) - R_EARTH).toLocaleString() + ' km';
      document.getElementById('stat-vel').innerText = v.toFixed(2) + ' km/s';

      requestAnimationFrame(draw);
    }}
    draw();
  </script>
</body>
</html>
"""

    @staticmethod
    def _generate_physics_demo(repo_name: str, tagline: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{repo_name} - Symplectic Phase-Space Simulation</title>
  <style>
    body {{ margin: 0; background: #0f172a; color: #e2e8f0; font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; }}
    header {{ padding: 12px 24px; background: #1e293b; display: flex; justify-content: space-between; align-items: center; }}
    h1 {{ margin: 0; font-size: 1.1rem; color: #a855f7; }}
    #container {{ display: flex; flex: 1; }}
    canvas {{ flex: 1; background: #020617; }}
    #sidebar {{ width: 300px; background: #111827; padding: 20px; }}
  </style>
</head>
<body>
  <header>
    <h1>⚛️ {repo_name} — Phase-Space Dynamic Trajectory</h1>
    <a href="https://github.com/Raj123-0/{repo_name}" target="_blank" style="color: #a855f7; text-decoration: none;">GitHub</a>
  </header>
  <div id="container">
    <canvas id="simCanvas"></canvas>
    <div id="sidebar">
      <h3>Hamiltonian Mechanics</h3>
      <p style="font-size: 0.85rem; color: #94a3b8;">Symplectic integrator conserving phase-space volume and energy bounds.</p>
      <div style="background: #1e293b; padding: 10px; border-radius: 6px; font-size: 0.85rem;">
        <div><strong>Total Energy H:</strong> <span id="energy-val" style="color: #a855f7;">--</span></div>
      </div>
    </div>
  </div>
  <script>
    const canvas = document.getElementById('simCanvas');
    const ctx = canvas.getContext('2d');
    let q = 1.8, p = 0.0, k = 1.0, m = 1.0, dt = 0.02;
    const history = [];

    function resize() {{
      canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
      canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    }}
    window.addEventListener('resize', resize);
    resize();

    function step() {{
      // Verlet symplectic step
      const f1 = -k * q;
      q = q + (p / m) * dt + 0.5 * (f1 / m) * dt * dt;
      const f2 = -k * q;
      p = p + 0.5 * (f1 + f2) * dt;

      history.push([q, p]);
      if (history.length > 500) history.shift();

      const cx = canvas.width / 2, cy = canvas.height / 2;
      const scale = Math.min(canvas.width, canvas.height) / 5;

      ctx.fillStyle = 'rgba(2, 6, 23, 0.15)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Phase-Space Orbit
      ctx.beginPath();
      for (let i = 0; i < history.length; i++) {{
        const x = cx + history[i][0] * scale;
        const y = cy - history[i][1] * scale;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }}
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Current State Point
      ctx.beginPath();
      ctx.arc(cx + q * scale, cy - p * scale, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#f43f5e';
      ctx.fill();

      const energy = 0.5 * (p * p) / m + 0.5 * k * (q * q);
      document.getElementById('energy-val').innerText = energy.toFixed(5) + ' J';

      requestAnimationFrame(step);
    }}
    step();
  </script>
</body>
</html>
"""

    @staticmethod
    def _generate_math_demo(repo_name: str, tagline: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{repo_name} - Math Explorer</title>
  <style>
    body {{ margin: 0; background: #0f172a; color: #e2e8f0; font-family: sans-serif; padding: 24px; }}
    header {{ border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    h1 {{ color: #38bdf8; margin: 0; }}
    input, button {{ background: #1e293b; border: 1px solid #475569; color: #fff; padding: 8px 14px; border-radius: 6px; font-size: 1rem; }}
    button {{ background: #0284c7; cursor: pointer; }}
    button:hover {{ background: #0369a1; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ padding: 10px; border: 1px solid #334155; text-align: left; }}
    th {{ background: #1e293b; color: #38bdf8; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>📐 {repo_name}</h1>
      <p style="color: #94a3b8; margin: 4px 0 0 0;">{tagline}</p>
    </div>
    <a href="https://github.com/Raj123-0/{repo_name}" target="_blank" style="color: #38bdf8; text-decoration: none;">GitHub</a>
  </header>
  <div style="margin-bottom: 16px;">
    <label>Compute Continued Fraction of &radic;D: </label>
    <input type="number" id="d-input" value="61" min="2" max="1000">
    <button onclick="compute()">Calculate Convergents</button>
  </div>
  <div id="output"></div>
  <script>
    function compute() {{
      const d = parseInt(document.getElementById('d-input').value);
      const m0 = Math.floor(Math.sqrt(d));
      if (m0 * m0 === d) {{
        document.getElementById('output').innerHTML = '<p>D is a perfect square; expansion terminates immediately.</p>';
        return;
      }}
      let m = 0, d_val = 1, a = m0;
      let period = [];
      for (let i = 0; i < 20; i++) {{
        m = d_val * a - m;
        d_val = Math.floor((d - m * m) / d_val);
        a = Math.floor((m0 + m) / d_val);
        period.push(a);
        if (a === 2 * m0) break;
      }}
      let html = '<p><strong>Period:</strong> [' + m0 + '; (' + period.join(', ') + ')]</p>';
      html += '<table><tr><th>k</th><th>a_k</th><th>p_k / q_k</th><th>Error</th></tr>';
      let p_prev = 1, p_curr = m0;
      let q_prev = 0, q_curr = 1;
      html += '<tr><td>0</td><td>' + m0 + '</td><td>' + p_curr + '/' + q_curr + '</td><td>' + (Math.abs(p_curr/q_curr - Math.sqrt(d))).toExponential(4) + '</td></tr>';
      for (let i = 0; i < period.length; i++) {{
        const ak = period[i];
        const p_next = ak * p_curr + p_prev;
        const q_next = ak * q_curr + q_prev;
        const err = Math.abs(p_next / q_next - Math.sqrt(d)).toExponential(4);
        html += '<tr><td>' + (i + 1) + '</td><td>' + ak + '</td><td>' + p_next + '/' + q_next + '</td><td>' + err + '</td></tr>';
        p_prev = p_curr; p_curr = p_next;
        q_prev = q_curr; q_curr = q_next;
      }}
      html += '</table>';
      document.getElementById('output').innerHTML = html;
    }}
    compute();
  </script>
</body>
</html>
"""

    @staticmethod
    def _generate_systems_demo(repo_name: str, tagline: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{repo_name} - StackVM Interactive REPL</title>
  <style>
    body {{ margin: 0; background: #0f172a; color: #f8fafc; font-family: monospace; padding: 24px; }}
    textarea {{ width: 100%; height: 120px; background: #1e293b; color: #38bdf8; border: 1px solid #475569; padding: 10px; box-sizing: border-box; font-family: monospace; font-size: 1rem; }}
    button {{ background: #0284c7; color: white; border: none; padding: 8px 16px; cursor: pointer; margin-top: 8px; font-weight: bold; border-radius: 4px; }}
    .stack-view {{ display: flex; gap: 8px; margin-top: 16px; }}
    .stack-elem {{ background: #334155; border: 1px solid #64748b; padding: 12px 18px; font-size: 1.2rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>💻 {repo_name} — StackVM Visualizer</h1>
  <p>{tagline}</p>
  <p>Bytecode Instructions (PUSH, ADD, SUB, MUL, DUP, HALT):</p>
  <textarea id="code">PUSH 15\nPUSH 25\nADD\nPUSH 2\nMUL\nHALT</textarea>
  <button onclick="run()">Execute Bytecode</button>
  <h3>Final Stack Memory:</h3>
  <div id="stack" class="stack-view"></div>
  <script>
    function run() {{
      const lines = document.getElementById('code').value.split('\\n');
      const stack = [];
      for (const raw of lines) {{
        const parts = raw.trim().split(/\\s+/);
        const op = parts[0].toUpperCase();
        if (op === 'PUSH') stack.push(parseInt(parts[1]) || 0);
        else if (op === 'ADD') stack.push(stack.pop() + stack.pop());
        else if (op === 'SUB') {{ const b = stack.pop(), a = stack.pop(); stack.push(a - b); }}
        else if (op === 'MUL') stack.push(stack.pop() * stack.pop());
        else if (op === 'DUP') stack.push(stack[stack.length - 1]);
        else if (op === 'HALT') break;
      }}
      document.getElementById('stack').innerHTML = stack.map(v => '<div class="stack-elem">' + v + '</div>').join('');
    }}
    run();
  </script>
</body>
</html>
"""

    @staticmethod
    def _generate_crypto_demo(repo_name: str, tagline: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{repo_name} - Shamir Secret Sharing Demo</title>
  <style>
    body {{ margin: 0; background: #0b0f19; color: #f1f5f9; font-family: sans-serif; padding: 24px; }}
    input, button {{ background: #1e293b; color: #fff; border: 1px solid #475569; padding: 8px 12px; border-radius: 6px; }}
    button {{ background: #10b981; border: none; cursor: pointer; font-weight: bold; }}
    .share-box {{ background: #1e293b; padding: 8px 12px; border-radius: 4px; margin: 4px 0; font-family: monospace; }}
  </style>
</head>
<body>
  <h1>🔐 {repo_name} — Threshold Secret Sharing</h1>
  <p>{tagline}</p>
  <div>
    <label>Secret Integer: </label>
    <input type="number" id="sec" value="424242">
    <button onclick="split()">Split into (k=3, n=5) Shares</button>
  </div>
  <h3>Generated Shares:</h3>
  <div id="shares"></div>
  <script>
    const P = 2147483647; // 2^31 - 1 Mersenne prime
    function split() {{
      const S = parseInt(document.getElementById('sec').value);
      const a1 = Math.floor(Math.random() * 100000) + 1;
      const a2 = Math.floor(Math.random() * 100000) + 1;
      let html = '';
      for (let x = 1; x <= 5; x++) {{
        const y = (S + a1 * x + a2 * x * x) % P;
        html += '<div class="share-box">Share #' + x + ': (' + x + ', ' + y + ')</div>';
      }}
      document.getElementById('shares').innerHTML = html;
    }}
    split();
  </script>
</body>
</html>
"""
