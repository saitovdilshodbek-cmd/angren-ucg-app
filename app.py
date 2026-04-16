import streamlit as st

st.set_page_config(page_title="Geo-Lab Jeofizik", layout="wide")

html_code = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geo-Lab | Jeofizik ve Geomekanik Laboratuvarı</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; font-family: 'Inter', sans-serif; color: #f1f5f9; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1rem; padding: 1rem; }
        .formula-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(129, 140, 248, 0.15); padding: 1rem; border-radius: 0.75rem; }
        .tab-active { border-bottom: 4px solid #818cf8; color: #818cf8; background-color: rgba(79, 70, 229, 0.1); }
        input[type=range] { width: 100%; }
        .delta-table th, .delta-table td { padding: 0.5rem; border: 1px solid #334155; text-align: center; }
        .delta-table th { background: #1e293b; color: #94a3b8; }
        input[type=number] { background: #1e293b; border: 1px solid #334155; color: white; padding: 0.5rem; border-radius: 0.5rem; width: 100%; }
        .hidden-canvas { display: none; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        <header class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 border border-indigo-500/30 flex justify-between">
            <div>
                <h1 class="text-3xl font-black text-white uppercase">Geo-Lab Jeofizik</h1>
                <p class="text-indigo-400 text-xs uppercase">Yoğunluk, Dayanım ve Geomekanik Simülasyonu</p>
            </div>
            <div class="text-right"><p class="text-green-400">● ÇEVRİMİÇİ</p></div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div class="lg:col-span-3 space-y-4">
                <div class="glass-panel">
                    <h3 class="text-xs font-bold uppercase text-slate-400 mb-3">Veri Filtresi</h3>
                    <div class="flex mb-4 rounded-lg overflow-hidden border border-slate-700">
                        <button onclick="switchTab('ucs')" id="tab-ucs" class="flex-1 py-2 text-xs font-bold tab-active">UCS</button>
                        <button onclick="switchTab('brazil')" id="tab-brazil" class="flex-1 py-2 text-xs font-bold text-slate-500">BREZİLYA</button>
                    </div>
                    <div id="checkbox-container" class="space-y-2"></div>
                </div>
                <div class="glass-panel">
                    <h3 class="text-cyan-400 font-bold text-xs mb-3">Yoğunluk Simülatörü</h3>
                    <div class="flex flex-col items-center gap-2">
                        <div style="width:120px; height:180px; border:3px solid #64748b; border-radius:0 0 40px 40px; position:relative;">
                            <div id="water-level" style="position:absolute; bottom:0; width:100%; background:#3b82f6aa; height:50%; transition:0.3s; display:flex; align-items:center; justify-content:center;">
                                <span id="rho-display" class="text-white font-bold">0.7 kg/L</span>
                            </div>
                        </div>
                        <div class="w-full">
                            <div class="flex justify-between text-xs"><span>KÜTLE (m)</span><span id="m-val" class="text-blue-400">6.0 kg</span></div>
                            <input type="range" id="m-slider" min="1" max="20" step="0.1" value="6" oninput="updateDensitySim()">
                            <div class="flex justify-between text-xs mt-2"><span>HACİM (V)</span><span id="v-val" class="text-blue-400">8.6 L</span></div>
                            <input type="range" id="v-slider" min="1" max="20" step="0.1" value="8.6" oninput="updateDensitySim()">
                        </div>
                    </div>
                </div>
                <!-- Hoek-Brown Panel -->
                <div class="glass-panel border-l-4 border-orange-500">
                    <h3 class="text-orange-400 font-bold text-xs mb-3 uppercase">Hoek-Brown & Geomekanik</h3>
                    <div class="space-y-2 text-xs">
                        <div><label class="text-slate-400">GSI</label> <input type="number" id="gsi" value="50" min="10" max="100" oninput="calcHoekBrown()" class="py-1"></div>
                        <div><label class="text-slate-400">mi</label> <input type="number" id="mi" value="10" min="1" max="35" oninput="calcHoekBrown()" class="py-1"></div>
                        <div><label class="text-slate-400">D (Örselenme)</label> <input type="number" id="D" value="0" min="0" max="1" step="0.1" oninput="calcHoekBrown()" class="py-1"></div>
                        <div><label class="text-slate-400">σci (MPa)</label> <input type="number" id="sigci" value="80" min="1" oninput="calcHoekBrown()" class="py-1"></div>
                        <hr class="border-slate-700 my-2">
                        <div><span class="text-slate-400">mb = </span><span id="mb-val" class="text-orange-300">-</span></div>
                        <div><span class="text-slate-400">s = </span><span id="s-val" class="text-orange-300">-</span></div>
                        <div><span class="text-slate-400">a = </span><span id="a-val" class="text-orange-300">-</span></div>
                        <div><label class="text-slate-400">σ3 (MPa)</label> <input type="number" id="sigma3" value="0" oninput="calcHoekBrown()" class="py-1"></div>
                        <div class="font-bold text-orange-300">σ1 = <span id="sigma1-val">-</span> MPa</div>
                        <hr class="border-slate-700 my-2">
                        <div><label class="text-slate-400">Elastisite Modülü (E)</label></div>
                        <div><span class="text-slate-400">E (GPa) = </span><span id="E-val" class="text-orange-300">-</span></div>
                        <p class="text-[10px] text-slate-500">Hoek & Diederichs (2006)</p>
                    </div>
                </div>
            </div>
            <div class="lg:col-span-9">
                <div class="glass-panel h-96 relative">
                    <canvas id="mainChart" width="800" height="400" style="width:100%; height:100%;"></canvas>
                </div>
                <div class="glass-panel mt-4">
                    <h3 class="text-blue-400 text-xs uppercase mb-2">Seçili Numuneler</h3>
                    <div id="sample-gallery" class="grid grid-cols-4 md:grid-cols-8 gap-2"></div>
                </div>
            </div>
        </div>

        <!-- Yashirin canvas (Brezilya grafigi) -->
        <canvas id="brazilChartCanvas" width="800" height="400" class="hidden-canvas"></canvas>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel"><h3 class="text-purple-400 text-sm">Yoğunluk (ρ)</h3><div class="formula-card text-center">ρ = m / V</div><input type="number" id="dens-m" placeholder="m (g)" oninput="calcDens()"><input type="number" id="dens-v" placeholder="V (cm³)" oninput="calcDens()"><div id="res-dens" class="text-center text-purple-300 font-bold">-</div></div>
            <div class="glass-panel"><h3 class="text-yellow-400 text-sm">Porozite</h3><div class="formula-card text-center">n = (1 - ρb/ρs)·100%</div><input type="number" id="rho-b" placeholder="ρb" oninput="calcPoro()"><input type="number" id="rho-s" placeholder="ρs" oninput="calcPoro()"><div id="res-poro" class="text-center text-yellow-300 font-bold">-</div></div>
            <div class="glass-panel"><h3 class="text-red-400 text-sm">Termal Deform.</h3><div class="formula-card text-center">ε = α·ΔT</div><input type="number" id="alpha" placeholder="α" oninput="calcStrain()"><input type="number" id="deltaT" placeholder="ΔT" oninput="calcStrain()"><div id="res-strain" class="text-center text-red-300 font-bold">-</div></div>
            <div class="glass-panel"><h3 class="text-green-400 text-sm">UCS Degrad.</h3><div class="formula-card text-center">σ(T)=σ0·e^(-βT)</div><input type="number" id="sig0" placeholder="σ0" oninput="calcDeg()"><input type="number" id="beta" placeholder="β" oninput="calcDeg()"><input type="number" id="temp" placeholder="T" oninput="calcDeg()"><div id="res-deg" class="text-center text-green-300 font-bold">-</div></div>
        </div>

        <div class="glass-panel">
            <h3 class="text-amber-400 font-bold text-sm uppercase">Kütle Kaybı (Δm) Analizi</h3>
            <div class="formula-card text-center text-2xl text-amber-300 py-3">Δm = (m₀ - mₜ) / m₀ × 100%</div>
            <table class="delta-table w-full">
                <thead><tr><th>Numune</th><th>25°C Kütle (g)</th><th>100°C Δm (%)</th><th>500°C Δm (%)</th><th>1000°C Δm (%)</th></tr></thead>
                <tbody id="delta-table-body"></tbody>
            </table>
        </div>

        <div class="glass-panel text-center">
            <h3 class="text-blue-400 font-bold text-sm uppercase mb-2">Akademik Rapor</h3>
            <button onclick="downloadWordReport()" class="bg-blue-600 hover:bg-blue-700 text-white py-3 px-8 rounded-xl font-bold">📄 Word (UCS + Brezilya + Geomekanik) İndir</button>
            <button onclick="downloadGraphsAsPNG()" class="bg-green-600 hover:bg-green-700 text-white py-3 px-8 rounded-xl font-bold ml-2">📥 Grafikleri PNG indir</button>
            <p class="text-xs text-slate-400 mt-2">Word'de UCS, Brezilya grafikleri, Δm tablosu, numune detayları ve geomekanik hesaplar bulunur.</p>
        </div>

        <div class="glass-panel">
            <h3 class="text-white font-black text-xl mb-4">Bilimsel Sonuç</h3>
            <div id="conclusion-text" class="text-slate-300 space-y-4">
                <p>Yüksek sıcaklık kayaçların fiziko-mekanik özelliklerini bozar. Kütle kaybı (Δm) ile UCS arasında ters korelasyon vardır. Bu çalışma UCG projelerinde termal duraylılık değerlendirmesine katkı sağlar.</p>
            </div>
        </div>
    </div>

    <script>
        const allDatasets = [
            { label: 'Kıltaşı UCS-1', data: [{x:718,y:25},{x:705,y:100},{x:693,y:500}], baseColor:0, diameter: 54.0, length: 110.0 },
            { label: 'Kıltaşı UCS-2', data: [{x:464,y:25},{x:456,y:100},{x:409,y:1000}], baseColor:40, diameter: 54.0, length: 108.0 },
            { label: 'Kumtaşı UCS-1', data: [{x:673,y:25},{x:667,y:100},{x:662,y:500}], baseColor:210, diameter: 54.0, length: 112.0 },
            { label: 'Kumtaşı UCS-2', data: [{x:701,y:25},{x:694,y:100},{x:667,y:1000}], baseColor:260, diameter: 54.0, length: 110.0 },
            { label: 'Kıltaşı Brezilya-1', data: [{x:197,y:25},{x:191,y:100},{x:174,y:1000}], baseColor:150, diameter: 54.0, length: 54.0 },
            { label: 'Kıltaşı Brezilya-2', data: [{x:196,y:25},{x:193,y:100},{x:191,y:500}], baseColor:80, diameter: 54.0, length: 52.0 },
            { label: 'Kumtaşı Brezilya-1', data: [{x:198,y:25},{x:196,y:100},{x:189,y:1000}], baseColor:330, diameter: 54.0, length: 55.0 },
            { label: 'Kumtaşı Brezilya-2', data: [{x:193,y:25},{x:193,y:100},{x:191,y:500}], baseColor:280, diameter: 54.0, length: 53.0 }
        ];

        let currentTab = 'ucs';
        const canvas = document.getElementById('mainChart');
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, { 
            type:'scatter', data:{datasets:[]}, options:{
                scales:{ x:{title:{display:true,text:'Kütle (g)'}}, y:{title:{display:true,text:'Sıcaklık (°C)'}} }
            }
        });

        // Yashirin Brezilya grafigi
        const brazilCanvas = document.getElementById('brazilChartCanvas');
        const brazilCtx = brazilCanvas.getContext('2d');
        const brazilChart = new Chart(brazilCtx, {
            type:'scatter', data:{datasets:[]}, options:{
                plugins:{title:{display:true,text:'Brezilya Testi'}},
                scales:{ x:{title:{text:'Kütle (g)'}}, y:{title:{text:'Sıcaklık (°C)'}} }
            }
        });

        function initBrazilChart() {
            const brazilDs = [];
            allDatasets.slice(4).forEach(ds => {
                brazilDs.push({ label: ds.label, data: ds.data, showLine: true,
                    borderColor: `hsl(${ds.baseColor},70%,50%)`, backgroundColor: `hsl(${ds.baseColor},70%,50%,0.5)`, pointRadius:6, tension:0.4 });
            });
            brazilChart.data.datasets = brazilDs;
            brazilChart.update();
        }

        function calcHoekBrown() {
            const GSI = parseFloat(document.getElementById('gsi').value) || 50;
            const mi = parseFloat(document.getElementById('mi').value) || 10;
            const D = parseFloat(document.getElementById('D').value) || 0;
            const sigci = parseFloat(document.getElementById('sigci').value) || 80;
            const sigma3 = parseFloat(document.getElementById('sigma3').value) || 0;

            const mb = mi * Math.exp((GSI - 100) / (28 - 14*D));
            const s = Math.exp((GSI - 100) / (9 - 3*D));
            const a = 0.5 + (Math.exp(-GSI/15) - Math.exp(-20/3))/6;
            document.getElementById('mb-val').innerText = mb.toFixed(3);
            document.getElementById('s-val').innerText = s.toExponential(3);
            document.getElementById('a-val').innerText = a.toFixed(3);

            const sigma1 = sigma3 + sigci * Math.pow(mb * sigma3 / sigci + s, a);
            document.getElementById('sigma1-val').innerText = sigma1.toFixed(2);

            const E = 100 * (1 - D/2) * Math.sqrt(sigci/100) * Math.pow(10, (GSI-10)/40);
            document.getElementById('E-val').innerText = E.toFixed(2);
        }

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
                        borderColor: `hsl(${ds.baseColor},70%,50%)`, backgroundColor: `hsl(${ds.baseColor},70%,50%,0.5)`, pointRadius:6, tension:0.4 });
                }
            });
            chart.data.datasets = active;
            chart.update();
        }

        function updateDensitySim() {
            const m = +document.getElementById('m-slider').value;
            const v = +document.getElementById('v-slider').value;
            document.getElementById('m-val').innerText = m.toFixed(1)+' kg';
            document.getElementById('v-val').innerText = v.toFixed(1)+' L';
            document.getElementById('rho-display').innerText = (m/v).toFixed(2)+' kg/L';
            document.getElementById('water-level').style.height = (v/20*100)+'%';
        }

        function calcDens(){ const m=+document.getElementById('dens-m').value||0, v=+document.getElementById('dens-v').value||0; document.getElementById('res-dens').innerText = v>0?(m/v).toFixed(3)+' g/cm³':'-'; }
        function calcPoro(){ const rb=+document.getElementById('rho-b').value||0, rs=+document.getElementById('rho-s').value||0; document.getElementById('res-poro').innerText = rs>0?((1-rb/rs)*100).toFixed(2)+' %':'-'; }
        function calcStrain(){ const a=+document.getElementById('alpha').value||0, d=+document.getElementById('deltaT').value||0; document.getElementById('res-strain').innerText = (a*d).toExponential(3); }
        function calcDeg(){ const s=+document.getElementById('sig0').value||0, b=+document.getElementById('beta').value||0, t=+document.getElementById('temp').value||0; document.getElementById('res-deg').innerText = (s*Math.exp(-b*t)).toFixed(2)+' MPa'; }

        function downloadGraphsAsPNG() {
            const linkMain = document.createElement('a'); linkMain.download = 'UCS_Grafik.png'; linkMain.href = canvas.toDataURL('image/png'); linkMain.click();
            setTimeout(() => { const linkBrazil = document.createElement('a'); linkBrazil.download = 'Brezilya_Grafik.png'; linkBrazil.href = brazilCanvas.toDataURL('image/png'); linkBrazil.click(); }, 200);
        }

        async function downloadWordReport() {
            chart.update(); brazilChart.update();
            await new Promise(r => setTimeout(r, 300));
            const mainImg = canvas.toDataURL('image/png');
            const brazilImg = brazilCanvas.toDataURL('image/png');
            const tableHtml = document.querySelector('.delta-table').outerHTML;
            const conclusion = document.getElementById('conclusion-text').innerHTML;
            const now = new Date().toLocaleString('tr-TR');

            let sampleRows = '';
            allDatasets.forEach(ds => {
                const p25 = ds.data.find(p=>p.y===25); const m0 = p25?p25.x:0;
                const d = ds.diameter||0, l = ds.length||0;
                const volume = Math.PI * Math.pow(d/20,2)*l;
                const density = volume>0 ? (m0/volume).toFixed(3) : '-';
                sampleRows += `<tr><td>${ds.label}</td><td>${d.toFixed(1)}</td><td>${l.toFixed(1)}</td><td>${volume.toFixed(2)}</td><td>${density}</td></tr>`;
            });

            const geoRows = `
                <tr><td>GSI</td><td>${document.getElementById('gsi').value}</td></tr>
                <tr><td>mi</td><td>${document.getElementById('mi').value}</td></tr>
                <tr><td>D</td><td>${document.getElementById('D').value}</td></tr>
                <tr><td>σci (MPa)</td><td>${document.getElementById('sigci').value}</td></tr>
                <tr><td>mb</td><td>${document.getElementById('mb-val').innerText}</td></tr>
                <tr><td>s</td><td>${document.getElementById('s-val').innerText}</td></tr>
                <tr><td>a</td><td>${document.getElementById('a-val').innerText}</td></tr>
                <tr><td>σ3 (MPa)</td><td>${document.getElementById('sigma3').value}</td></tr>
                <tr><td>σ1 (MPa)</td><td>${document.getElementById('sigma1-val').innerText}</td></tr>
                <tr><td>E (GPa)</td><td>${document.getElementById('E-val').innerText}</td></tr>
            `;

            const fullHtml = `
            <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Geo-Lab Rapor</title>
            <style>body{font-family:Calibri; margin:2cm;} table{border-collapse:collapse; width:100%;} th,td{border:1px solid #333; padding:8px;} img{max-width:100%;}</style>
            </head><body>
                <h1>Geo-Lab Jeofizik ve Geomekanik Raporu</h1><p>${now}</p>
                <h2>UCS Grafiği</h2><img src="${mainImg}">
                <h2>Brezilya Grafiği</h2><img src="${brazilImg}">
                <h2>Numune Özellikleri</h2><table><tr><th>Numune</th><th>Çap(mm)</th><th>Uzunluk(mm)</th><th>Hacim(cm³)</th><th>Yoğunluk(g/cm³)</th></tr>${sampleRows}</table>
                <h2>Kütle Kaybı Tablosu</h2>${tableHtml}
                <h2>Geomekanik Hesaplamalar (Hoek-Brown)</h2>
                <table><tr><th>Parametre</th><th>Değer</th></tr>${geoRows}</table>
                <p><em>Formüller: mb = mi·exp((GSI-100)/(28-14D)); s = exp((GSI-100)/(9-3D)); a = 0.5 + (e^(-GSI/15)-e^(-20/3))/6; E = 100·(1-D/2)·√(σci/100)·10^((GSI-10)/40).</em></p>
                <h2>Bilimsel Sonuç</h2>${conclusion}
                <h2>Kaynakça (APA 7)</h2><ul><li>Hoek, E., Carranza-Torres, C., & Corkum, B. (2002). Hoek-Brown failure criterion-2002 edition. NARMS-TAC.</li><li>Hoek, E., & Diederichs, M. S. (2006). Empirical estimation of rock mass modulus. IJRM.</li></ul>
            </body></html>`;

            const blob = new Blob([fullHtml], {type: 'application/msword'});
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `GeoLab_Rapor_${new Date().toISOString().slice(0,10)}.doc`;
            document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(a.href);
        }

        window.onload = () => { switchTab('ucs'); updateDensitySim(); renderDeltaTable(); initBrazilChart(); calcHoekBrown(); };
    </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=1300, scrolling=True)
