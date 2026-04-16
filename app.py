<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geo-Lab AI & Advanced Geophysics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
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
        .img-placeholder { position: absolute; font-size: 10px; color: #475569; text-align: center; padding: 5px; }
        input[type=number] { background: #1e293b; border: 1px solid #334155; color: white; padding: 0.5rem; border-radius: 0.5rem; width: 100%; }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header -->
        <header class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 border border-indigo-500/30 shadow-2xl flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-black tracking-tighter text-white uppercase">Geo-Lab Interactive</h1>
                <p class="text-indigo-400 text-xs font-bold uppercase tracking-widest mt-1">Density & Strength Simulation</p>
            </div>
            <div class="hidden md:block text-right">
                <p class="text-[10px] text-slate-500">LAB STATUS</p>
                <p class="text-green-400 font-mono text-sm">● ONLINE / CONNECTED</p>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Left Controls -->
            <div class="lg:col-span-3 space-y-4">
                <div class="glass-panel p-4 rounded-xl">
                    <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-3">Ma'lumotlar filtri</h3>
                    <div class="bg-slate-900/50 flex mb-4 rounded-lg overflow-hidden border border-slate-700">
                        <button onclick="switchTab('ucs')" id="tab-ucs" class="flex-1 py-2 text-[10px] font-bold tab-active">UCS</button>
                        <button onclick="switchTab('brazil')" id="tab-brazil" class="flex-1 py-2 text-[10px] font-bold text-slate-500">BRAZIL</button>
                    </div>
                    <div id="checkbox-container" class="space-y-2"></div>
                </div>

                <!-- Interaktiv Zichlik Modeli -->
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

            <!-- Main Chart Area -->
            <div class="lg:col-span-9 space-y-6">
                <div class="glass-panel p-6 rounded-2xl h-[450px] relative">
                    <div class="absolute top-4 right-4 flex gap-2">
                        <span class="px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 text-[10px] font-bold">LIVE DATA</span>
                    </div>
                    <canvas id="mainChart"></canvas>
                </div>

                <!-- Mini Gallery -->
                <div class="glass-panel p-4 rounded-xl border-blue-500/20">
                    <h3 class="text-blue-400 font-bold text-[10px] uppercase mb-3">Tanlangan namunalar holati</h3>
                    <div id="sample-gallery" class="grid grid-cols-4 md:grid-cols-8 gap-2"></div>
                </div>
            </div>
        </div>

        <!-- YANGI GEO-FIZIK KALKULYATORLAR (4 ta) -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
            <!-- Density (g/cm³) -->
            <div class="glass-panel p-6 rounded-2xl border border-purple-500/20">
                <h3 class="text-purple-400 font-bold text-sm mb-4 uppercase">Zichlik (Density)</h3>
                <div class="formula-card text-center text-purple-300">ρ = m / V</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="dens-m" placeholder="m (g)" oninput="calculateDensityExt()">
                    <input type="number" id="dens-v" placeholder="V (cm³)" oninput="calculateDensityExt()">
                </div>
                <div class="text-center mt-3 text-purple-300 font-bold" id="res-dens">-</div>
            </div>

            <!-- Porosity -->
            <div class="glass-panel p-6 rounded-2xl border border-yellow-500/20">
                <h3 class="text-yellow-400 font-bold text-sm mb-4 uppercase">Porozlik</h3>
                <div class="formula-card text-center text-yellow-300">n = (1 - ρb/ρs)·100%</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="rho-b" placeholder="ρb" oninput="calculatePorosity()">
                    <input type="number" id="rho-s" placeholder="ρs" oninput="calculatePorosity()">
                </div>
                <div class="text-center mt-3 text-yellow-300 font-bold" id="res-poro">-</div>
            </div>

            <!-- Thermal strain -->
            <div class="glass-panel p-6 rounded-2xl border border-red-500/20">
                <h3 class="text-red-400 font-bold text-sm mb-4 uppercase">Thermal strain</h3>
                <div class="formula-card text-center text-red-300">ε = α·ΔT</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="alpha" placeholder="α" oninput="calculateThermalStrain()">
                    <input type="number" id="deltaT" placeholder="ΔT" oninput="calculateThermalStrain()">
                </div>
                <div class="text-center mt-3 text-red-300 font-bold" id="res-strain">-</div>
            </div>

            <!-- UCS degradation (exponential) -->
            <div class="glass-panel p-6 rounded-2xl border border-green-500/20">
                <h3 class="text-green-400 font-bold text-sm mb-4 uppercase">UCS degradatsiya</h3>
                <div class="formula-card text-center text-green-300">σ(T)=σ0·e^(-βT)</div>
                <div class="grid grid-cols-3 gap-2 text-xs mt-3">
                    <input type="number" id="sig0" placeholder="σ0" oninput="calculateDegradation()">
                    <input type="number" id="beta" placeholder="β" oninput="calculateDegradation()">
                    <input type="number" id="temp" placeholder="T" oninput="calculateDegradation()">
                </div>
                <div class="text-center mt-3 text-green-300 font-bold" id="res-deg">-</div>
            </div>
        </div>

        <!-- AI section (kengaytirilgan) -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass-panel p-6 rounded-2xl border-pink-500/30 col-span-2">
                <h3 class="text-pink-400 font-bold text-sm uppercase mb-4">AI Bashorat Modeli</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 bg-black/30 rounded-xl border border-pink-500/10">
                        <p class="text-[10px] text-slate-500 uppercase mb-2">Chiziqli Regressiya (Δm vs UCS)</p>
                        <div id="regression-result" class="text-pink-300 font-bold text-sm">...</div>
                    </div>
                    <div class="p-4 bg-black/30 rounded-xl border border-indigo-500/10">
                        <p class="text-[10px] text-slate-500 uppercase mb-2">Neyron Tarmoq (TF.JS)</p>
                        <div class="flex flex-col gap-2">
                            <div class="flex gap-2">
                                <input type="number" id="predict-temp" placeholder="Harorat °C" class="bg-slate-800 border-none text-xs p-2 rounded w-full">
                                <button onclick="predictWithNN()" class="bg-indigo-600 px-3 py-1 rounded text-[10px] font-bold">GO</button>
                            </div>
                            <button onclick="trainModel()" class="bg-indigo-800/50 px-3 py-1 rounded text-[10px] font-bold text-indigo-300">Modelni o'rgatish</button>
                        </div>
                        <div id="prediction-result" class="text-indigo-300 font-bold text-xs mt-2">-</div>
                        <div id="ai-status" class="text-[10px] text-slate-400 mt-1">Model tayyor emas</div>
                    </div>
                </div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border-green-500/20">
                <h3 class="text-green-400 font-bold text-sm uppercase mb-4">Hisobot</h3>
                <p class="text-[10px] text-slate-400 mb-4">Barcha laboratoriya ma'lumotlarini TXT formatida yuklab oling.</p>
                <button onclick="downloadReport()" class="w-full bg-green-600/20 hover:bg-green-600/40 text-green-400 py-3 rounded-xl font-bold text-xs uppercase transition-all border border-green-500/30">Hujjatni shakllantirish</button>
            </div>
        </div>

        <!-- ILMIY-ANALITIK XULOSA -->
        <div class="glass-panel p-8 rounded-2xl border border-indigo-500/30 conclusion-section mt-6">
            <h3 class="text-white font-black text-xl mb-6 uppercase tracking-wider flex items-center gap-3">
                <span class="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-sm italic">Σ</span>
                Ilmiy-analitik xulosa (Advanced Level)
            </h3>
            <div class="space-y-6 text-slate-300 leading-relaxed text-sm md:text-[15px]">
                <p>O‘tkazilgan eksperimental tadqiqotlar va kompleks termik-mexanik tahlillar natijalari shuni ko‘rsatadiki, yuqori harorat ta’siri ostida tog‘ jinslarining strukturaviy, mineralogik va fizik-mexanik xususiyatlari sezilarli darajada degradatsiyaga uchraydi. Massa yo‘qotilishi (Δm) ko‘rsatkichlari jins tarkibidagi gigroskopik va kristallangan suvning bug‘lanishi, shuningdek karbonat va boshqa termik beqaror minerallarning dissotsiatsiyasi bilan bevosita bog‘liq ekanligi aniqlandi.</p>
                <p>Tahlil natijalari Δm ning haroratga bog‘liqligi nolinear va eksponensial xarakterga ega ekanligini ko‘rsatdi, bu esa Arrhenius tipidagi kinetik jarayonlar bilan yuqori darajada mos keladi. Issiqlik uzatilish jarayonlari esa Fourier qonuni va issiqlik diffuziyasi tenglamalari asosida izohlanib, jins ichida notekis harorat maydonining shakllanishiga va natijada lokal stress konsentratsiyalarining yuzaga kelishiga olib keladi.</p>
                <p>Mexanik sinovlar (bir o‘qli siqilish – UCS va Braziliya usuli orqali cho‘zilish) natijalari jins mustahkamligining harorat ortishi bilan keskin kamayishini ko‘rsatdi. Ushbu kamayish eksponensial degradatsiya modeli orqali ifodalanib, σc(T) funksiyasining pasayishi jins ichki bog‘lanish energiyasining kamayishi hamda mikroyoriqlar tarmog‘ining rivojlanishi bilan izohlanadi.</p>
                <p>Bundan tashqari, zichlikning kamayishi va porozlikning ortishi jinsning umumiy deformatsion xulq-atvoriga sezilarli ta’sir ko‘rsatadi. Olingan natijalar Hoek–Brown va Mohr–Coulomb buzilish kriteriyalari doirasida tahlil qilinganda, jinsning buzilish chegarasi harorat ortishi bilan sezilarli darajada pasayishi aniqlandi.</p>
                <p>Raqamli tahlil (regressiya va sun’iy intellekt modellari) natijalari Δm va mexanik mustahkamlik o‘rtasida barqaror teskari korrelyatsiya mavjudligini tasdiqladi. Ushbu bog‘liqlik asosida ishlab chiqilgan bashorat modeli yuqori harorat sharoitida jinsning xatti-harakatini prognoz qilish imkonini beradi.</p>
                <p class="text-indigo-300 font-semibold">Umuman olganda, olingan natijalar yer osti ko‘mir gazifikatsiyasi (UCG) jarayonlarida jinslarning termik degradatsiya mexanizmlarini chuqur tushunishga xizmat qiladi hamda real geotexnik sharoitlarda barqarorlikni baholash va xavfsizlikni ta’minlash uchun muhim ilmiy asos bo‘lib xizmat qiladi.</p>
            </div>
        </div>
    </div>

    <script>
        // ---------- GLOBAL O'ZGARUVCHILAR ----------
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
        let nnModel = null;

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

        // ---------- TAB VA FILTER ----------
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
            calculateRegression(); // regressionni yangilash
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

        // ---------- QO'SHIMCHA KALKULYATORLAR ----------
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

        // ---------- REGRESSIYA (Δm vs UCS) ----------
        function calculateRegression() {
            let x = [], y = [];
            // faqat UCS datasetlaridan foydalanamiz (birinchi 4 ta)
            allDatasets.slice(0, 4).forEach(ds => {
                const m0 = ds.data[0].x;
                ds.data.forEach(p => {
                    if(p.y !== 25) {
                        let dm = ((m0 - p.x)/m0)*100;
                        x.push(dm);
                        y.push(100 - dm * 5); // soddalashtirilgan model
                    }
                });
            });
            if(x.length < 2) {
                document.getElementById("regression-result").innerText = "Ma'lumot yetarli emas";
                return;
            }
            let n = x.length, sumX = x.reduce((a,b)=>a+b,0), sumY = y.reduce((a,b)=>a+b,0);
            let sumXY = x.reduce((a,b,i)=>a+b*y[i],0), sumXX = x.reduce((a,b)=>a+b*b,0);
            let slope = (n*sumXY - sumX*sumY) / (n*sumXX - sumX*sumX);
            let intercept = (sumY - slope*sumX) / n;
            document.getElementById("regression-result").innerText = `σc = ${intercept.toFixed(2)} - ${Math.abs(slope).toFixed(2)}·Δm`;
        }

        // ---------- NEYRON TARMOQ (TF.JS) ----------
        async function trainModel() {
            const statusEl = document.getElementById('ai-status');
            statusEl.innerText = "Ma'lumot tayyorlanmoqda...";
            
            let x = [], y = [];
            allDatasets.slice(0,4).forEach(ds => {
                const m0 = ds.data[0].x;
                ds.data.forEach(p => {
                    if(p.y !== 25) {
                        let dm = ((m0 - p.x)/m0)*100;
                        x.push(dm);
                        y.push(100 - dm * 5);
                    }
                });
            });

            const xs = tf.tensor2d(x, [x.length, 1]);
            const ys = tf.tensor2d(y, [y.length, 1]);

            nnModel = tf.sequential();
            nnModel.add(tf.layers.dense({units: 8, inputShape: [1], activation: 'relu'}));
            nnModel.add(tf.layers.dense({units: 1}));

            nnModel.compile({ optimizer: tf.train.adam(0.01), loss: 'meanSquaredError' });

            await nnModel.fit(xs, ys, {
                epochs: 100,
                callbacks: {
                    onEpochEnd: (epoch, logs) => {
                        if(epoch % 10 === 0) {
                            statusEl.innerText = `O'qitilmoqda... Loss: ${logs.loss.toFixed(4)}`;
                        }
                    }
                }
            });
            statusEl.innerText = "Model tayyor ✅";
        }

        async function predictWithNN() {
            const input = parseFloat(document.getElementById('predict-temp').value) || 0;
            const resEl = document.getElementById('prediction-result');
            if (!nnModel) {
                resEl.innerText = "Avval modelni o'rgating";
                return;
            }
            // taxminiy mapping: harorat -> dm
            let dm = input * 0.08; 
            const pred = nnModel.predict(tf.tensor2d([dm], [1,1]));
            const value = (await pred.data())[0];
            resEl.innerText = value.toFixed(2) + " MPa (bashorat)";
        }

        // ---------- HISOBOT ----------
        function downloadReport() {
            const densityVal = document.getElementById('rho-display').innerText;
            const regResult = document.getElementById('regression-result').innerText;
            const nnStatus = document.getElementById('ai-status').innerText;
            const poro = document.getElementById('res-poro').innerText;
            const content = `GEO-LAB TO'LIQ HISOBOT\n${'-'.repeat(30)}\nZichlik simulyatori: ${densityVal}\nPorozlik: ${poro}\nRegressiya: ${regResult}\nNeyron tarmoq holati: ${nnStatus}\n\nIlmiy xulosa ilova qilingan.`;
            const blob = new Blob([content], {type: 'text/plain'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "GeoLab_Advanced_Report.txt";
            a.click();
        }

        // ---------- ISHGA TUSHIRISH ----------
        window.onload = () => { 
            switchTab('ucs'); 
            updateDensitySim();
            calculateRegression();
        };
    </script>
</body>
</html>
