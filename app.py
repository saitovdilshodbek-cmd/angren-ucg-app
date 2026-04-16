import streamlit as st

st.set_page_config(page_title="Geo-Lab Jeofizik", layout="wide")

html_code = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geo-Lab | Jeofizik Laboratuvarı</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; font-family: 'Inter', sans-serif; color: #f1f5f9; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1rem; padding: 1rem; }
        .formula-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(129, 140, 248, 0.15); padding: 1rem; border-radius: 0.75rem; }
        .tab-active { border-bottom: 4px solid #818cf8; color: #818cf8; }
        input[type=range] { width: 100%; }
        .delta-table th, .delta-table td { padding: 0.5rem; border: 1px solid #334155; text-align: center; }
        .delta-table th { background: #1e293b; color: #94a3b8; }
        button { cursor: pointer; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        <header class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 border border-indigo-500/30">
            <h1 class="text-3xl font-black text-white uppercase">Geo-Lab Jeofizik</h1>
            <p class="text-indigo-400 text-xs uppercase">Yoğunluk ve Dayanım Simülasyonu</p>
        </header>

        <!-- Filtr va Grafik -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div class="lg:col-span-3">
                <div class="glass-panel">
                    <h3 class="text-xs font-bold uppercase text-slate-400 mb-3">Veri Filtresi</h3>
                    <div class="flex mb-4 rounded-lg overflow-hidden border border-slate-700">
                        <button onclick="switchTab('ucs')" id="tab-ucs" class="flex-1 py-2 text-xs font-bold tab-active">UCS</button>
                        <button onclick="switchTab('brazil')" id="tab-brazil" class="flex-1 py-2 text-xs font-bold text-slate-500">BREZİLYA</button>
                    </div>
                    <div id="checkbox-container" class="space-y-2"></div>
                </div>
            </div>
            <div class="lg:col-span-9">
                <div class="glass-panel h-96 relative">
                    <canvas id="mainChart"></canvas>
                </div>
            </div>
        </div>

        <!-- 4 ta kalkulyator -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel"><h3 class="text-purple-400 font-bold text-sm">Yoğunluk (ρ)</h3><div class="formula-card text-center">ρ = m / V</div><input type="number" id="dens-m" placeholder="m (g)" oninput="calcDens()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><input type="number" id="dens-v" placeholder="V (cm³)" oninput="calcDens()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><div id="res-dens" class="text-center text-purple-300 font-bold">-</div></div>
            <div class="glass-panel"><h3 class="text-yellow-400 font-bold text-sm">Porozite</h3><div class="formula-card text-center">n = (1 - ρb/ρs)·100%</div><input type="number" id="rho-b" placeholder="ρb" oninput="calcPoro()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><input type="number" id="rho-s" placeholder="ρs" oninput="calcPoro()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><div id="res-poro" class="text-center text-yellow-300 font-bold">-</div></div>
            <div class="glass-panel"><h3 class="text-red-400 font-bold text-sm">Termal Deform.</h3><div class="formula-card text-center">ε = α·ΔT</div><input type="number" id="alpha" placeholder="α" oninput="calcStrain()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><input type="number" id="deltaT" placeholder="ΔT" oninput="calcStrain()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><div id="res-strain" class="text-center text-red-300 font-bold">-</div></div>
            <div class="glass-panel"><h3 class="text-green-400 font-bold text-sm">UCS Degrad.</h3><div class="formula-card text-center">σ(T)=σ0·e^(-βT)</div><input type="number" id="sig0" placeholder="σ0" oninput="calcDeg()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><input type="number" id="beta" placeholder="β" oninput="calcDeg()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><input type="number" id="temp" placeholder="T" oninput="calcDeg()" class="w-full my-1 bg-slate-800 rounded p-1 text-white"><div id="res-deg" class="text-center text-green-300 font-bold">-</div></div>
        </div>

        <!-- Δm jadvali -->
        <div class="glass-panel">
            <h3 class="text-amber-400 font-bold text-sm uppercase">Kütle Kaybı (Δm) Analizi</h3>
            <div class="text-2xl text-amber-300 text-center my-2">Δm = (m₀ - mₜ) / m₀ × 100%</div>
            <table class="delta-table w-full">
                <thead><tr><th>Numune</th><th>25°C Kütle (g)</th><th>100°C Δm (%)</th><th>500°C Δm (%)</th><th>1000°C Δm (%)</th></tr></thead>
                <tbody id="delta-table-body"></tbody>
            </table>
        </div>

        <!-- Word eksport -->
        <div class="glass-panel text-center">
            <button onclick="downloadWord()" class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-6 rounded-lg font-bold">📄 Word (APA Kaynakçalı) İndir</button>
        </div>

        <!-- Xulosa -->
        <div class="glass-panel">
            <h3 class="text-white font-black text-xl">Bilimsel Sonuç</h3>
            <p class="text-slate-300">Yüksek sıcaklık etkisi altında kayaçların fiziko-mekanik özellikleri bozulur. Kütle kaybı (Δm) ile UCS arasında ters korelasyon vardır. Bu çalışma UCG projeleri için termal duraylılık değerlendirmesine katkı sağlar.</p>
        </div>
    </div>

    <script>
        const allDatasets = [
            { label: 'Kireçtaşı UCS-1', data: [{x:718,y:25},{x:705,y:100},{x:693,y:500}], baseColor:0 },
            { label: 'Kireçtaşı UCS-2', data: [{x:464,y:25},{x:456,y:100},{x:409,y:1000}], baseColor:40 },
            { label: 'Kumtaşı UCS-1', data: [{x:673,y:25},{x:667,y:100},{x:662,y:500}], baseColor:210 },
            { label: 'Kumtaşı UCS-2', data: [{x:701,y:25},{x:694,y:100},{x:667,y:1000}], baseColor:260 },
            { label: 'Kireçtaşı Brezilya-1', data: [{x:197,y:25},{x:191,y:100},{x:174,y:1000}], baseColor:150 },
            { label: 'Kireçtaşı Brezilya-2', data: [{x:196,y:25},{x:193,y:100},{x:191,y:500}], baseColor:80 },
            { label: 'Kumtaşı Brezilya-1', data: [{x:198,y:25},{x:196,y:100},{x:189,y:1000}], baseColor:330 },
            { label: 'Kumtaşı Brezilya-2', data: [{x:193,y:25},{x:193,y:100},{x:191,y:500}], baseColor:280 }
        ];
        let currentTab = 'ucs';
        const ctx = document.getElementById('mainChart').getContext('2d');
        const chart = new Chart(ctx, { type:'scatter', data:{datasets:[]}, options:{
            scales:{ x:{title:{display:true,text:'Kütle (g)'}}, y:{title:{display:true,text:'Sıcaklık (°C)'}} }
        }});

        function renderDeltaTable() {
            const tbody = document.getElementById('delta-table-body');
            tbody.innerHTML = '';
            allDatasets.forEach(ds => {
                const row = document.createElement('tr');
                const name = document.createElement('td'); name.innerText = ds.label; row.appendChild(name);
                const p25 = ds.data.find(p=>p.y===25); const m0 = p25?p25.x:null;
                const m0c = document.createElement('td'); m0c.innerText = m0?m0.toFixed(1):'-'; row.appendChild(m0c);
                [100,500,1000].forEach(T => {
                    const cell = document.createElement('td');
                    const pt = ds.data.find(p=>p.y===T);
                    if(m0 && pt) { const d = ((m0-pt.x)/m0)*100; cell.innerText = d.toFixed(2)+'%'; cell.style.color = `hsl(0,80%,${60-Math.min(d/20,1)*20}%)`; }
                    else cell.innerText = '-';
                    row.appendChild(cell);
                });
                tbody.appendChild(row);
            });
        }

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tab-ucs').className = tab==='ucs'? 'flex-1 py-2 text-xs font-bold tab-active' : 'flex-1 py-2 text-xs font-bold text-slate-500';
            document.getElementById('tab-brazil').className = tab==='brazil'? 'flex-1 py-2 text-xs font-bold tab-active' : 'flex-1 py-2 text-xs font-bold text-slate-500';
            renderCheckboxes(); updateChart();
        }

        function renderCheckboxes() {
            const cont = document.getElementById('checkbox-container');
            cont.innerHTML = '';
            const start = currentTab==='ucs'?0:4, end = currentTab==='ucs'?4:8;
            for(let i=start; i<end; i++) {
                const div = document.createElement('div'); div.className = "flex items-center gap-2 p-2 bg-slate-800/30 rounded";
                div.innerHTML = `<input type="checkbox" checked onchange="updateChart()" data-index="${i}" class="accent-indigo-500"> <span class="text-xs">${allDatasets[i].label}</span>`;
                cont.appendChild(div);
            }
        }

        function updateChart() {
            const active = [];
            document.querySelectorAll('#checkbox-container input').forEach(cb => {
                if(cb.checked) {
                    const ds = allDatasets[cb.dataset.index];
                    active.push({ label: ds.label, data: ds.data, showLine: true,
                        borderColor: `hsl(${ds.baseColor},70%,50%)`,
                        backgroundColor: `hsl(${ds.baseColor},70%,50%,0.5)`, pointRadius:6, tension:0.4 });
                }
            });
            chart.data.datasets = active; chart.update();
        }

        function calcDens(){ const m=+document.getElementById('dens-m').value||0, v=+document.getElementById('dens-v').value||0; document.getElementById('res-dens').innerText = v>0?(m/v).toFixed(3)+' g/cm³':'-'; }
        function calcPoro(){ const rb=+document.getElementById('rho-b').value||0, rs=+document.getElementById('rho-s').value||0; document.getElementById('res-poro').innerText = rs>0?((1-rb/rs)*100).toFixed(2)+' %':'-'; }
        function calcStrain(){ const a=+document.getElementById('alpha').value||0, d=+document.getElementById('deltaT').value||0; document.getElementById('res-strain').innerText = (a*d).toExponential(3); }
        function calcDeg(){ const s=+document.getElementById('sig0').value||0, b=+document.getElementById('beta').value||0, t=+document.getElementById('temp').value||0; document.getElementById('res-deg').innerText = (s*Math.exp(-b*t)).toFixed(2)+' MPa'; }

        async function downloadWord() {
            const canvas = document.getElementById('mainChart');
            const img = canvas.toDataURL('image/png');
            const table = document.querySelector('.delta-table').outerHTML;
            const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Geo-Lab Rapor</title></head><body>
                <h1>Geo-Lab Jeofizik Raporu</h1><img src="${img}" style="max-width:100%"><h2>Kütle Kaybı Tablosu</h2>${table}
                <h2>Kaynakça (APA 7)</h2><ul><li>ASTM D7012-14e1</li><li>Hoek & Brown (1997)</li><li>Ulusay & Hudson (2007)</li></ul>
            </body></html>`;
            const blob = new Blob([html], {type:'application/msword'});
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'GeoLab_Rapor.doc'; a.click();
        }

        window.onload = () => { switchTab('ucs'); renderDeltaTable(); };
    </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=1300, scrolling=True)
