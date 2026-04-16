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
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .formula-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(129, 140, 248, 0.15); padding: 1rem; border-radius: 0.75rem; font-family: serif; }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { height: 18px; width: 18px; border-radius: 50%; background: #818cf8; }
        .tab-active { border-bottom: 4px solid #818cf8; color: #818cf8; background-color: rgba(79, 70, 229, 0.1); }
        .cylinder-container { position: relative; width: 120px; height: 180px; border: 3px solid #64748b; border-top: none; border-radius: 0 0 40px 40px; overflow: hidden; }
        .water { position: absolute; bottom: 0; left: 0; width: 100%; background: #3b82f6aa; transition: height 0.3s; }
        .delta-table th, .delta-table td { padding: 0.5rem; border: 1px solid #334155; }
        .delta-table th { background: #1e293b; color: #94a3b8; }
        input[type=number] { background: #1e293b; border: 1px solid #334155; color: white; padding: 0.5rem; border-radius: 0.5rem; width: 100%; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        <header class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 border border-indigo-500/30 flex justify-between">
            <div>
                <h1 class="text-3xl font-black text-white uppercase">Geo-Lab Jeofizik</h1>
                <p class="text-indigo-400 text-xs uppercase">Yoğunluk ve Dayanım Simülasyonu</p>
            </div>
            <div class="text-right"><p class="text-green-400">● ÇEVRİMİÇİ</p></div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div class="lg:col-span-3 space-y-4">
                <div class="glass-panel p-4 rounded-xl">
                    <h3 class="text-xs font-bold uppercase text-slate-400 mb-3">Veri Filtresi</h3>
                    <div class="flex mb-4 rounded-lg overflow-hidden border border-slate-700">
                        <button onclick="switchTab('ucs')" id="tab-ucs" class="flex-1 py-2 text-xs font-bold tab-active">UCS</button>
                        <button onclick="switchTab('brazil')" id="tab-brazil" class="flex-1 py-2 text-xs font-bold text-slate-500">BREZİLYA</button>
                    </div>
                    <div id="checkbox-container" class="space-y-2"></div>
                </div>

                <div class="glass-panel p-5 rounded-2xl border-cyan-500/30">
                    <h3 class="text-cyan-400 font-bold text-xs mb-4 uppercase">Yoğunluk Simülatörü</h3>
                    <div class="flex flex-col items-center gap-4">
                        <div class="cylinder-container">
                            <div class="cylinder-top" style="height:20px; background:#1e293b; border-radius:50%;"></div>
                            <div id="water-level" class="water" style="height:50%;"><span id="rho-display" class="text-white font-bold">0.7 kg/L</span></div>
                        </div>
                        <div class="w-full space-y-3">
                            <div><span class="text-xs text-slate-400">KÜTLE (m)</span> <span id="m-val" class="text-blue-400">6.0 kg</span>
                                <input type="range" id="m-slider" min="1" max="20" step="0.1" value="6" oninput="updateDensitySim()"></div>
                            <div><span class="text-xs text-slate-400">HACİM (V)</span> <span id="v-val" class="text-blue-400">8.6 L</span>
                                <input type="range" id="v-slider" min="1" max="20" step="0.1" value="8.6" oninput="updateDensitySim()"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-9">
                <div class="glass-panel p-6 rounded-2xl h-96 relative">
                    <canvas id="mainChart"></canvas>
                </div>
                <div class="glass-panel p-4 rounded-xl border-blue-500/20 mt-4">
                    <h3 class="text-blue-400 text-xs uppercase mb-2">Seçili Numuneler</h3>
                    <div id="sample-gallery" class="grid grid-cols-4 md:grid-cols-8 gap-2"></div>
                </div>
            </div>
        </div>

        <!-- 4 Hesaplayıcı -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <div class="glass-panel p-4"><h3 class="text-purple-400 text-sm">Yoğunluk (ρ)</h3><div class="formula-card text-center text-purple-300">ρ = m / V</div><input type="number" id="dens-m" placeholder="m (g)" oninput="calcDens()"><input type="number" id="dens-v" placeholder="V (cm³)" oninput="calcDens()"><div id="res-dens" class="text-center text-purple-300 font-bold">-</div></div>
            <div class="glass-panel p-4"><h3 class="text-yellow-400 text-sm">Porozite</h3><div class="formula-card text-center text-yellow-300">n = (1 - ρb/ρs)·100%</div><input type="number" id="rho-b" placeholder="ρb" oninput="calcPoro()"><input type="number" id="rho-s" placeholder="ρs" oninput="calcPoro()"><div id="res-poro" class="text-center text-yellow-300 font-bold">-</div></div>
            <div class="glass-panel p-4"><h3 class="text-red-400 text-sm">Termal Deformasyon</h3><div class="formula-card text-center text-red-300">ε = α·ΔT</div><input type="number" id="alpha" placeholder="α" oninput="calcStrain()"><input type="number" id="deltaT" placeholder="ΔT" oninput="calcStrain()"><div id="res-strain" class="text-center text-red-300 font-bold">-</div></div>
            <div class="glass-panel p-4"><h3 class="text-green-400 text-sm">UCS Degradasyonu</h3><div class="formula-card text-center text-green-300">σ(T)=σ0·e^(-βT)</div><input type="number" id="sig0" placeholder="σ0" oninput="calcDeg()"><input type="number" id="beta" placeholder="β" oninput="calcDeg()"><input type="number" id="temp" placeholder="T" oninput="calcDeg()"><div id="res-deg" class="text-center text-green-300 font-bold">-</div></div>
        </div>

        <!-- Δm Tablosu -->
        <div class="glass-panel p-6 rounded-2xl border border-amber-500/30">
            <h3 class="text-amber-400 font-bold text-sm uppercase">Kütle Kaybı (Δm) Analizi</h3>
            <div class="formula-card text-center text-2xl text-amber-300 py-3">Δm = (m₀ - mₜ) / m₀ × 100%</div>
            <table class="delta-table w-full">
                <thead><tr><th>Numune</th><th>25°C Kütle (g)</th><th>100°C Δm (%)</th><th>500°C Δm (%)</th><th>1000°C Δm (%)</th></tr></thead>
                <tbody id="delta-table-body"></tbody>
            </table>
        </div>

        <!-- Rapor İndir -->
        <div class="glass-panel p-6 rounded-2xl border border-blue-500/20 text-center">
            <h3 class="text-blue-400 font-bold text-sm uppercase mb-2">Akademik Rapor</h3>
            <button onclick="downloadWordReport()" class="bg-blue-600 hover:bg-blue-700 text-white py-3 px-8 rounded-xl font-bold">📄 Word (APA Kaynakçalı) İndir</button>
            <p class="text-xs text-slate-400 mt-2">Grafik, tablo, formüller ve APA 7 kaynakçası ile</p>
        </div>

        <!-- Akademik Sonuç -->
        <div class="glass-panel p-8 rounded-2xl border border-indigo-500/30">
            <h3 class="text-white font-black text-xl mb-4">Bilimsel-Analitik Sonuç</h3>
            <div id="conclusion-text" class="text-slate-300 space-y-4">
                <p>Yapılan deneysel araştırmalar ve termo-mekanik analizler, yüksek sıcaklığın kayaçların fiziko-mekanik özelliklerini önemli ölçüde bozduğunu göstermektedir. Kütle kaybı (Δm) ile UCS arasında ters korelasyon mevcuttur. Bu çalışma, yeraltı kömür gazlaştırma (UCG) projelerinde termal duraylılığın değerlendirilmesi için bilimsel temel sunmaktadır.</p>
                <p>Referanslar: ASTM D7012, Hoek & Brown (1997), Ulusay & Hudson (2007).</p>
            </div>
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

        async function downloadWordReport() {
            const canvas = document.getElementById('mainChart');
            const chartImg = canvas.toDataURL('image/png');
            const tableHtml = document.querySelector('.delta-table').outerHTML;
            const conclusion = document.getElementById('conclusion-text').innerHTML;
            const now = new Date().toLocaleString('tr-TR');

            const fullHtml = `
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8"><title>Geo-Lab Akademik Rapor</title>
            <style>body{font-family:Calibri; margin:2cm;} table{border-collapse:collapse; width:100%;} th,td{border:1px solid #333; padding:8px;} img{max-width:100%;}</style>
            </head><body>
                <h1>Geo-Lab Jeofizik Analiz Raporu</h1>
                <p><strong>Oluşturulma:</strong> ${now}</p>
                <h2>1. Kütle – Sıcaklık Grafiği</h2>
                <img src="${chartImg}" alt="Grafik">
                <h2>2. Kütle Kaybı (Δm) Tablosu</h2>
                ${tableHtml}
                <h2>3. Temel Formüller</h2>
                <p>Yoğunluk: ρ = m / V &nbsp;|&nbsp; Porozite: n = (1 - ρb/ρs)·100%</p>
                <p>Termal deformasyon: ε = α·ΔT &nbsp;|&nbsp; UCS degradasyonu: σ(T) = σ0·e<sup>(-βT)</sup></p>
                <p>Kütle kaybı: Δm = (m₀ - mₜ) / m₀ × 100%</p>
                <h2>4. Bilimsel Sonuç</h2>
                <div>${conclusion}</div>
                <h2>5. Kaynakça (APA 7)</h2>
                <ul>
                    <li>ASTM D7012-14e1. (2020). Standard Test Method for Compressive Strength of Intact Rock Core Specimens.</li>
                    <li>Hoek, E., & Brown, E. T. (1997). Practical estimates of rock mass strength. <i>Int. J. Rock Mech. Min. Sci.</i>, 34(8), 1165–1186.</li>
                    <li>Ulusay, R., & Hudson, J. A. (2007). <i>The Complete ISRM Suggested Methods for Rock Characterization</i>. ISRM.</li>
                    <li>Jaeger, J. C., Cook, N. G. W., & Zimmerman, R. W. (2007). <i>Fundamentals of Rock Mechanics</i> (4th ed.). Blackwell.</li>
                </ul>
            </body></html>`;

            const blob = new Blob([fullHtml], {type: 'application/msword'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `GeoLab_Rapor_${new Date().toISOString().slice(0,10)}.doc`;
            a.click();
        }

        window.onload = () => { switchTab('ucs'); updateDensitySim(); renderDeltaTable(); };
    </script>
</body>
</html>
"""

st.components.v1.html(html_code, height=1300, scrolling=True)
