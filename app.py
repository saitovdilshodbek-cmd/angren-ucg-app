<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geo-Lab | Geofizika Laboratoriyasi</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0f172a; font-family: 'Inter', sans-serif; color: #f1f5f9; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .formula-card { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(129, 140, 248, 0.15); padding: 1rem; border-radius: 0.75rem; font-family: serif; }
        
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]:focus { outline: none; }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 6px; cursor: pointer; background: #334155; border-radius: 3px; }
        input[type=range]::-webkit-slider-thumb { height: 18px; width: 18px; border-radius: 50%; background: #818cf8; cursor: pointer; -webkit-appearance: none; margin-top: -6px; box-shadow: 0 0 10px rgba(129, 140, 248, 0.5); }

        .tab-active { border-bottom: 4px solid #818cf8; color: #818cf8; background-color: rgba(79, 70, 229, 0.1); }
        
        .cylinder-container { position: relative; width: 120px; height: 180px; border: 3px solid #64748b; border-top: none; border-radius: 0 0 40px 40px; background: rgba(255,255,255,0.05); overflow: hidden; }
        .cylinder-top { position: absolute; top: -10px; left: -3px; width: calc(100% + 6px); height: 20px; border: 3px solid #64748b; border-radius: 50%; background: #1e293b; z-index: 10; }
        .water { position: absolute; bottom: 0; left: 0; width: 100%; background: linear-gradient(180deg, #3b82f6aa 0%, #1d4ed8aa 100%); transition: height 0.3s ease; display: flex; align-items: center; justify-content: center; }
        .bubbles { position: absolute; width: 100%; height: 100%; pointer-events: none; }
        .bubble { position: absolute; background: rgba(255,255,255,0.3); border-radius: 50%; animation: float 2s infinite ease-in; }

        @keyframes float {
            0% { transform: translateY(100%) scale(0.5); opacity: 0; }
            50% { opacity: 0.5; }
            100% { transform: translateY(-100%) scale(1.2); opacity: 0; }
        }

        .sample-img-container { position: relative; width: 100%; aspect-ratio: 1; background: #1e293b; border-radius: 0.5rem; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,0.1); }
        input[type=number] { background: #1e293b; border: 1px solid #334155; color: white; padding: 0.5rem; border-radius: 0.5rem; width: 100%; }
        
        .delta-table th, .delta-table td { padding: 0.5rem 0.75rem; text-align: center; border: 1px solid #334155; }
        .delta-table th { background: #1e293b; color: #94a3b8; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; }
        .delta-table td { font-size: 0.75rem; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header -->
        <header class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 border border-indigo-500/30 shadow-2xl flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-black tracking-tighter text-white uppercase">Geo-Lab Geofizika</h1>
                <p class="text-indigo-400 text-xs font-bold uppercase tracking-widest mt-1">Zichlik va mustahkamlik simulyatsiyasi</p>
            </div>
            <div class="hidden md:block text-right">
                <p class="text-[10px] text-slate-500">LAB STATUS</p>
                <p class="text-green-400 font-mono text-sm">● ONLINE / FAOL</p>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Chap panel: Filtr + Zichlik -->
            <div class="lg:col-span-3 space-y-4">
                <div class="glass-panel p-4 rounded-xl">
                    <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-3">Ma'lumotlar filtri</h3>
                    <div class="bg-slate-900/50 flex mb-4 rounded-lg overflow-hidden border border-slate-700">
                        <button onclick="switchTab('ucs')" id="tab-ucs" class="flex-1 py-2 text-[10px] font-bold tab-active">UCS</button>
                        <button onclick="switchTab('brazil')" id="tab-brazil" class="flex-1 py-2 text-[10px] font-bold text-slate-500">BRAZIL</button>
                    </div>
                    <div id="checkbox-container" class="space-y-2"></div>
                </div>

                <!-- Zichlik simulyatori -->
                <div class="glass-panel p-5 rounded-2xl border-cyan-500/30">
                    <h3 class="text-cyan-400 font-bold text-xs mb-6 uppercase flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.183.244l-.28.19a2 2 0 00-.596 2.48l.15.305A11.061 11.061 0 008.145 20H15.854a11.061 11.061 0 004.006-1.57l.15-.306a2 2 0 00-.596-2.48l-.28-.19z"/></svg>
                        Zichlik Simulyatori
                    </h3>
                    
                    <div class="flex flex-col md:flex-row items-center gap-6">
                        <div class="flex-shrink-0">
                            <div class="cylinder-container">
                                <div class="cylinder-top"></div>
                                <div id="water-level" class="water" style="height: 50%;">
                                    <div class="bubbles" id="bubbles-container"></div>
                                    <span id="rho-display" class="text-white font-black text-xs drop-shadow-md">0.7 kg/L</span>
                                </div>
                            </div>
                        </div>

                        <div class="flex-1 w-full space-y-6">
                            <div class="formula-card text-center mb-4">
                                <span class="text-xl text-blue-300">ρ = m / V</span>
                            </div>
                            
                            <div class="space-y-4">
                                <div>
                                    <div class="flex justify-between text-[10px] text-slate-400 mb-1">
                                        <span>MASSA (m)</span>
                                        <span id="m-val" class="text-blue-400 font-bold">6.0 kg</span>
                                    </div>
                                    <input type="range" id="m-slider" min="1" max="20" step="0.1" value="6" oninput="updateDensitySim()">
                                </div>
                                <div>
                                    <div class="flex justify-between text-[10px] text-slate-400 mb-1">
                                        <span>HAJM (V)</span>
                                        <span id="v-val" class="text-blue-400 font-bold">8.6 L</span>
                                    </div>
                                    <input type="range" id="v-slider" min="1" max="20" step="0.1" value="8.6" oninput="updateDensitySim()">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Asosiy grafik -->
            <div class="lg:col-span-9 space-y-6">
                <div class="glass-panel p-6 rounded-2xl h-[450px] relative">
                    <div class="absolute top-4 right-4 flex gap-2">
                        <span class="px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 text-[10px] font-bold">JONLI MA'LUMOT</span>
                    </div>
                    <canvas id="mainChart"></canvas>
                </div>

                <!-- Mini galereya -->
                <div class="glass-panel p-4 rounded-xl border-blue-500/20">
                    <h3 class="text-blue-400 font-bold text-[10px] uppercase mb-3">Tanlangan namunalar</h3>
                    <div id="sample-gallery" class="grid grid-cols-4 md:grid-cols-8 gap-2"></div>
                </div>
            </div>
        </div>

        <!-- 4 ta geofizik kalkulyator -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
            <!-- Zichlik (g/cm³) -->
            <div class="glass-panel p-6 rounded-2xl border border-purple-500/20">
                <h3 class="text-purple-400 font-bold text-sm mb-4 uppercase">Zichlik (ρ)</h3>
                <div class="formula-card text-center text-purple-300">ρ = m / V</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="dens-m" placeholder="m (g)" oninput="calculateDensityExt()">
                    <input type="number" id="dens-v" placeholder="V (cm³)" oninput="calculateDensityExt()">
                </div>
                <div class="text-center mt-3 text-purple-300 font-bold" id="res-dens">-</div>
            </div>

            <!-- Porozlik -->
            <div class="glass-panel p-6 rounded-2xl border border-yellow-500/20">
                <h3 class="text-yellow-400 font-bold text-sm mb-4 uppercase">Porozlik</h3>
                <div class="formula-card text-center text-yellow-300">n = (1 - ρb/ρs)·100%</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="rho-b" placeholder="ρb (g/cm³)" oninput="calculatePorosity()">
                    <input type="number" id="rho-s" placeholder="ρs (g/cm³)" oninput="calculatePorosity()">
                </div>
                <div class="text-center mt-3 text-yellow-300 font-bold" id="res-poro">-</div>
            </div>

            <!-- Termal deformatsiya -->
            <div class="glass-panel p-6 rounded-2xl border border-red-500/20">
                <h3 class="text-red-400 font-bold text-sm mb-4 uppercase">Termal deformatsiya</h3>
                <div class="formula-card text-center text-red-300">ε = α·ΔT</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="alpha" placeholder="α (1/°C)" oninput="calculateThermalStrain()">
                    <input type="number" id="deltaT" placeholder="ΔT (°C)" oninput="calculateThermalStrain()">
                </div>
                <div class="text-center mt-3 text-red-300 font-bold" id="res-strain">-</div>
            </div>

            <!-- UCS degradatsiyasi -->
            <div class="glass-panel p-6 rounded-2xl border border-green-500/20">
                <h3 class="text-green-400 font-bold text-sm mb-4 uppercase">UCS degradatsiyasi</h3>
                <div class="formula-card text-center text-green-300">σ(T) = σ0·e^(-βT)</div>
                <div class="grid grid-cols-3 gap-2 text-xs mt-3">
                    <input type="number" id="sig0" placeholder="σ0 (MPa)" oninput="calculateDegradation()">
                    <input type="number" id="beta" placeholder="β" oninput="calculateDegradation()">
                    <input type="number" id="temp" placeholder="T (°C)" oninput="calculateDegradation()">
                </div>
                <div class="text-center mt-3 text-green-300 font-bold" id="res-deg">-</div>
            </div>
        </div>

        <!-- Δm formulasi va jadvali -->
        <div class="glass-panel p-6 rounded-2xl border border-amber-500/30">
            <h3 class="text-amber-400 font-bold text-sm uppercase mb-4 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                Massa yo'qotilishi (Δm) tahlili
            </h3>
            
            <div class="formula-card text-center mb-6 py-4">
                <div class="text-2xl text-amber-300">
                    Δm = (m₀ - mₜ) / m₀ × 100%
                </div>
                <p class="text-[10px] text-slate-400 mt-2">m₀ – 25°C dagi boshlang'ich massa, mₜ – T haroratdagi massa</p>
            </div>

            <div class="overflow-x-auto">
                <table class="delta-table w-full">
                    <thead>
                        <tr>
                            <th>Namuna</th>
                            <th>25°C da massa (g)</th>
                            <th>100°C Δm (%)</th>
                            <th>500°C Δm (%)</th>
                            <th>1000°C Δm (%)</th>
                        </tr>
                    </thead>
                    <tbody id="delta-table-body"></tbody>
                </table>
            </div>
            <p class="text-[10px] text-slate-500 mt-2">* Δm qiymatlari foizda ifodalangan. "-" ma'lumot mavjud emas.</p>
        </div>

        <!-- Hisobot yuklash -->
        <div class="glass-panel p-6 rounded-2xl border border-blue-500/20">
            <h3 class="text-blue-400 font-bold text-sm uppercase mb-4">Hisobot yuklash</h3>
            <button onclick="downloadReport()" class="w-full bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 py-3 rounded-xl font-bold text-xs uppercase transition-all border border-blue-500/30">
                📄 TXT hisobot yuklab olish
            </button>
        </div>

        <!-- Ilmiy xulosa (statik) -->
        <div class="glass-panel p-8 rounded-2xl border border-indigo-500/30 mt-6">
            <h3 class="text-white font-black text-xl mb-6 uppercase tracking-wider flex items-center gap-3">
                <span class="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-sm italic">Σ</span>
                Ilmiy-analitik xulosa
            </h3>
            <div class="space-y-6 text-slate-300 leading-relaxed text-sm md:text-[15px]">
                <p>O‘tkazilgan eksperimental tadqiqotlar va termo-mexanik tahlillar shuni ko‘rsatadiki, yuqori harorat ta’sirida tog‘ jinslarining fizik-mexanik xususiyatlari sezilarli darajada yomonlashadi. Massa yo‘qotilishi (Δm) jins tarkibidagi suv va gazlarning chiqib ketishi bilan bog‘liq.</p>
                <p>Harorat ortishi bilan bir o‘qli siqilish mustahkamligi (UCS) pasayadi, bu jins ichki bog‘lanish kuchlarining zaiflashuvi va mikro-yoriqlar rivojlanishi bilan izohlanadi.</p>
                <p>Olingan natijalar yer osti muhandislik loyihalarida termik barqarorlikni baholash uchun muhim ahamiyatga ega.</p>
            </div>
        </div>
    </div>

    <script>
        // ---------- MA'LUMOTLAR ----------
        const allDatasets = [
            { label: 'Ohaktosh UCS-1', data: [{x: 718, y: 25}, {x: 705, y: 100}, {x: 693, y: 500}], baseColor: 0 },
            { label: 'Ohaktosh UCS-2', data: [{x: 464, y: 25}, {x: 456, y: 100}, {x: 409, y: 1000}], baseColor: 40 },
            { label: 'Qumtosh UCS-1', data: [{x: 673, y: 25}, {x: 667, y: 100}, {x: 662, y: 500}], baseColor: 210 },
            { label: 'Qumtosh UCS-2', data: [{x: 701, y: 25}, {x: 694, y: 100}, {x: 667, y: 1000}], baseColor: 260 },
            { label: 'Limestone Brazil-1', data: [{x: 197, y: 25}, {x: 191, y: 100}, {x: 174, y: 1000}], baseColor: 150 },
            { label: 'Limestone Brazil-2', data: [{x: 196, y: 25}, {x: 193, y: 100}, {x: 191, y: 500}], baseColor: 80 },
            { label: 'Sandstone Brazil-1', data: [{x: 198, y: 25}, {x: 196, y: 100}, {x: 189, y: 1000}], baseColor: 330 },
            { label: 'Sandstone Brazil-2', data: [{x: 193, y: 25}, {x: 193, y: 100}, {x: 191, y: 500}], baseColor: 280 }
        ];

        let currentTab = 'ucs';

        // Chart.js
        const ctx = document.getElementById('mainChart').getContext('2d');
        const mainChart = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: [] },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: '#1e293b' }, title: { display: true, text: 'Massa (g)', color: '#94a3b8' } },
                    y: { grid: { color: '#1e293b' }, title: { display: true, text: 'Harorat (°C)', color: '#94a3b8' } }
                },
                plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } }, position: 'bottom' } }
            }
        });

        // ---------- Δm JADVALI ----------
        function renderDeltaTable() {
            const tbody = document.getElementById('delta-table-body');
            tbody.innerHTML = '';
            allDatasets.forEach(ds => {
                const row = document.createElement('tr');
                const nameCell = document.createElement('td');
                nameCell.className = 'text-left font-medium text-slate-300';
                nameCell.innerText = ds.label;
                row.appendChild(nameCell);
                
                const point25 = ds.data.find(p => p.y === 25);
                const m0 = point25 ? point25.x : null;
                
                const m0Cell = document.createElement('td');
                m0Cell.innerText = m0 !== null ? m0.toFixed(1) : '-';
                m0Cell.className = 'text-slate-400';
                row.appendChild(m0Cell);
                
                [100, 500, 1000].forEach(T => {
                    const cell = document.createElement('td');
                    const pointT = ds.data.find(p => p.y === T);
                    if (m0 !== null && pointT) {
                        const mT = pointT.x;
                        const delta = ((m0 - mT) / m0) * 100;
                        cell.innerText = delta.toFixed(2) + '%';
                        const intensity = Math.min(delta / 20, 1);
                        cell.style.color = `hsl(${0}, 80%, ${60 - intensity*20}%)`;
                        cell.style.fontWeight = 'bold';
                    } else {
                        cell.innerText = '-';
                        cell.style.color = '#64748b';
                    }
                    row.appendChild(cell);
                });
                tbody.appendChild(row);
            });
        }

        // ---------- TAB VA FILTR ----------
        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tab-ucs').className = tab === 'ucs' ? "flex-1 py-2 text-[10px] font-bold tab-active" : "flex-1 py-2 text-[10px] font-bold text-slate-500";
            document.getElementById('tab-brazil').className = tab === 'brazil' ? "flex-1 py-2 text-[10px] font-bold tab-active" : "flex-1 py-2 text-[10px] font-bold text-slate-500";
            renderCheckboxes();
            updateChartDisplay();
        }

        function renderCheckboxes() {
            const container = document.getElementById('checkbox-container');
            container.innerHTML = '';
            const start = currentTab === 'ucs' ? 0 : 4;
            const end = currentTab === 'ucs' ? 4 : 8;
            for(let i = start; i < end; i++) {
                const div = document.createElement('div');
                div.className = "flex items-center gap-2 p-2 bg-slate-800/30 rounded border border-slate-700 cursor-pointer hover:bg-slate-700/50 transition-all";
                div.innerHTML = `<input type="checkbox" checked onchange="updateChartDisplay()" data-index="${i}" class="w-3 h-3 accent-indigo-500"><span class="text-[10px] text-slate-300 font-medium">${allDatasets[i].label}</span>`;
                div.onclick = (e) => { if(e.target.tagName !== 'INPUT') { const cb = div.querySelector('input'); cb.checked = !cb.checked; updateChartDisplay(); } };
                container.appendChild(div);
            }
        }

        function updateChartDisplay() {
            const activeDatasets = [];
            const gallery = document.getElementById('sample-gallery');
            gallery.innerHTML = '';
            
            document.querySelectorAll('#checkbox-container input').forEach(cb => {
                if(cb.checked) {
                    const idx = cb.dataset.index;
                    const dsData = allDatasets[idx];
                    activeDatasets.push({
                        label: dsData.label,
                        data: dsData.data,
                        showLine: true,
                        borderColor: `hsl(${dsData.baseColor}, 70%, 50%)`,
                        backgroundColor: `hsl(${dsData.baseColor}, 70%, 50%, 0.5)`,
                        pointRadius: 6,
                        tension: 0.4
                    });

                    const thumb = document.createElement('div');
                    thumb.className = "sample-img-container h-12";
                    thumb.innerHTML = `<div class="text-[8px] text-slate-500 uppercase text-center">${dsData.label.split(' ')[0]}</div>`;
                    gallery.appendChild(thumb);
                }
            });

            mainChart.data.datasets = activeDatasets;
            mainChart.update();
        }

        // ---------- ZICHLIK SIMULYATORI ----------
        function updateDensitySim() {
            const m = parseFloat(document.getElementById('m-slider').value);
            const v = parseFloat(document.getElementById('v-slider').value);
            const rho = m / v;

            document.getElementById('m-val').innerText = m.toFixed(1) + " kg";
            document.getElementById('v-val').innerText = v.toFixed(1) + " L";
            document.getElementById('rho-display').innerText = rho.toFixed(2) + " kg/L";

            const heightPercent = (v / 20) * 100;
            document.getElementById('water-level').style.height = heightPercent + "%";

            const bubblesContainer = document.getElementById('bubbles-container');
            bubblesContainer.innerHTML = '';
            const bubbleCount = Math.floor(rho * 10);
            for(let i = 0; i < bubbleCount; i++) {
                const b = document.createElement('div');
                b.className = 'bubble';
                b.style.left = Math.random() * 100 + "%";
                b.style.width = b.style.height = (Math.random() * 6 + 2) + "px";
                b.style.animationDelay = Math.random() * 2 + "s";
                bubblesContainer.appendChild(b);
            }
        }

        // ---------- KALKULYATORLAR ----------
        function calculateDensityExt() {
            const m = parseFloat(document.getElementById('dens-m').value) || 0;
            const v = parseFloat(document.getElementById('dens-v').value) || 0;
            if (v > 0) document.getElementById('res-dens').innerText = (m / v).toFixed(3) + " g/cm³";
            else document.getElementById('res-dens').innerText = '-';
        }

        function calculatePorosity() {
            const rb = parseFloat(document.getElementById('rho-b').value) || 0;
            const rs = parseFloat(document.getElementById('rho-s').value) || 0;
            if (rs > 0) document.getElementById('res-poro').innerText = ((1 - rb / rs) * 100).toFixed(2) + " %";
            else document.getElementById('res-poro').innerText = '-';
        }

        function calculateThermalStrain() {
            const alpha = parseFloat(document.getElementById('alpha').value) || 0;
            const dT = parseFloat(document.getElementById('deltaT').value) || 0;
            document.getElementById('res-strain').innerText = (alpha * dT).toExponential(3);
        }

        function calculateDegradation() {
            const sig0 = parseFloat(document.getElementById('sig0').value) || 0;
            const beta = parseFloat(document.getElementById('beta').value) || 0;
            const T = parseFloat(document.getElementById('temp').value) || 0;
            document.getElementById('res-deg').innerText = (sig0 * Math.exp(-beta * T)).toFixed(2) + " MPa";
        }

        // ---------- HISOBOT ----------
        function downloadReport() {
            const densityVal = document.getElementById('rho-display').innerText;
            const poro = document.getElementById('res-poro').innerText;
            const strain = document.getElementById('res-strain').innerText;
            const deg = document.getElementById('res-deg').innerText;
            
            const content = `GEO-LAB HISOBOTI\n${'-'.repeat(30)}\nSana: ${new Date().toLocaleString()}\n\nZichlik simulyatori: ${densityVal}\nPorozlik: ${poro}\nTermal deformatsiya: ${strain}\nUCS degradatsiyasi: ${deg}\n\nΔm jadvali ma'lumotlari ilova qilingan.`;
            
            const blob = new Blob([content], {type: 'text/plain'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `GeoLab_Hisobot_${new Date().toISOString().slice(0,10)}.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }

        // ---------- ISHGA TUSHIRISH ----------
        window.onload = () => { 
            switchTab('ucs'); 
            updateDensitySim();
            renderDeltaTable();
        };
    </script>
</body>
</html>
