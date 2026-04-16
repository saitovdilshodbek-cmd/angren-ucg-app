<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geo-Lab | Jeofizik Laboratuvarı</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- MathJax formüller için -->
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
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
                <h1 class="text-3xl font-black tracking-tighter text-white uppercase">Geo-Lab Jeofizik</h1>
                <p class="text-indigo-400 text-xs font-bold uppercase tracking-widest mt-1">Yoğunluk ve Dayanım Simülasyonu</p>
            </div>
            <div class="hidden md:block text-right">
                <p class="text-[10px] text-slate-500">LAB DURUMU</p>
                <p class="text-green-400 font-mono text-sm">● ÇEVRİMİÇİ / AKTİF</p>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Sol Panel -->
            <div class="lg:col-span-3 space-y-4">
                <div class="glass-panel p-4 rounded-xl">
                    <h3 class="text-[10px] font-bold uppercase text-slate-400 mb-3">Veri Filtresi</h3>
                    <div class="bg-slate-900/50 flex mb-4 rounded-lg overflow-hidden border border-slate-700">
                        <button onclick="switchTab('ucs')" id="tab-ucs" class="flex-1 py-2 text-[10px] font-bold tab-active">UCS</button>
                        <button onclick="switchTab('brazil')" id="tab-brazil" class="flex-1 py-2 text-[10px] font-bold text-slate-500">BREZİLYA</button>
                    </div>
                    <div id="checkbox-container" class="space-y-2"></div>
                </div>

                <!-- Yoğunluk Simülatörü -->
                <div class="glass-panel p-5 rounded-2xl border-cyan-500/30">
                    <h3 class="text-cyan-400 font-bold text-xs mb-6 uppercase flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.183.244l-.28.19a2 2 0 00-.596 2.48l.15.305A11.061 11.061 0 008.145 20H15.854a11.061 11.061 0 004.006-1.57l.15-.306a2 2 0 00-.596-2.48l-.28-.19z"/></svg>
                        Yoğunluk Simülatörü
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
                                        <span>KÜTLE (m)</span>
                                        <span id="m-val" class="text-blue-400 font-bold">6.0 kg</span>
                                    </div>
                                    <input type="range" id="m-slider" min="1" max="20" step="0.1" value="6" oninput="updateDensitySim()">
                                </div>
                                <div>
                                    <div class="flex justify-between text-[10px] text-slate-400 mb-1">
                                        <span>HACİM (V)</span>
                                        <span id="v-val" class="text-blue-400 font-bold">8.6 L</span>
                                    </div>
                                    <input type="range" id="v-slider" min="1" max="20" step="0.1" value="8.6" oninput="updateDensitySim()">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Ana Grafik -->
            <div class="lg:col-span-9 space-y-6">
                <div class="glass-panel p-6 rounded-2xl h-[450px] relative">
                    <div class="absolute top-4 right-4 flex gap-2">
                        <span class="px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 text-[10px] font-bold">CANLI VERİ</span>
                    </div>
                    <canvas id="mainChart"></canvas>
                </div>

                <!-- Mini Galeri -->
                <div class="glass-panel p-4 rounded-xl border-blue-500/20">
                    <h3 class="text-blue-400 font-bold text-[10px] uppercase mb-3">Seçili Numuneler</h3>
                    <div id="sample-gallery" class="grid grid-cols-4 md:grid-cols-8 gap-2"></div>
                </div>
            </div>
        </div>

        <!-- 4 Jeofizik Hesaplayıcı -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
            <div class="glass-panel p-6 rounded-2xl border border-purple-500/20">
                <h3 class="text-purple-400 font-bold text-sm mb-4 uppercase">Yoğunluk (ρ)</h3>
                <div class="formula-card text-center text-purple-300">ρ = m / V</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="dens-m" placeholder="m (g)" oninput="calculateDensityExt()">
                    <input type="number" id="dens-v" placeholder="V (cm³)" oninput="calculateDensityExt()">
                </div>
                <div class="text-center mt-3 text-purple-300 font-bold" id="res-dens">-</div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border border-yellow-500/20">
                <h3 class="text-yellow-400 font-bold text-sm mb-4 uppercase">Porozite</h3>
                <div class="formula-card text-center text-yellow-300">n = (1 - ρb/ρs)·100%</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="rho-b" placeholder="ρb (g/cm³)" oninput="calculatePorosity()">
                    <input type="number" id="rho-s" placeholder="ρs (g/cm³)" oninput="calculatePorosity()">
                </div>
                <div class="text-center mt-3 text-yellow-300 font-bold" id="res-poro">-</div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border border-red-500/20">
                <h3 class="text-red-400 font-bold text-sm mb-4 uppercase">Termal Deformasyon</h3>
                <div class="formula-card text-center text-red-300">ε = α·ΔT</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="alpha" placeholder="α (1/°C)" oninput="calculateThermalStrain()">
                    <input type="number" id="deltaT" placeholder="ΔT (°C)" oninput="calculateThermalStrain()">
                </div>
                <div class="text-center mt-3 text-red-300 font-bold" id="res-strain">-</div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border border-green-500/20">
                <h3 class="text-green-400 font-bold text-sm mb-4 uppercase">UCS Degradasyonu</h3>
                <div class="formula-card text-center text-green-300">σ(T) = σ0·e^(-βT)</div>
                <div class="grid grid-cols-3 gap-2 text-xs mt-3">
                    <input type="number" id="sig0" placeholder="σ0 (MPa)" oninput="calculateDegradation()">
                    <input type="number" id="beta" placeholder="β" oninput="calculateDegradation()">
                    <input type="number" id="temp" placeholder="T (°C)" oninput="calculateDegradation()">
                </div>
                <div class="text-center mt-3 text-green-300 font-bold" id="res-deg">-</div>
            </div>
        </div>

        <!-- Δm Tablosu -->
        <div class="glass-panel p-6 rounded-2xl border border-amber-500/30">
            <h3 class="text-amber-400 font-bold text-sm uppercase mb-4 flex items-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                Kütle Kaybı (Δm) Analizi
            </h3>
            
            <div class="formula-card text-center mb-6 py-4">
                <div class="text-2xl text-amber-300">
                    $$\Delta m = \frac{m_0 - m_T}{m_0} \times 100\%$$
                </div>
                <p class="text-[10px] text-slate-400 mt-2">m₀ – 25°C'deki başlangıç kütlesi, mₜ – T sıcaklığındaki kütle</p>
            </div>

            <div class="overflow-x-auto">
                <table class="delta-table w-full">
                    <thead>
                        <tr>
                            <th>Numune</th>
                            <th>25°C'de Kütle (g)</th>
                            <th>100°C Δm (%)</th>
                            <th>500°C Δm (%)</th>
                            <th>1000°C Δm (%)</th>
                        </tr>
                    </thead>
                    <tbody id="delta-table-body"></tbody>
                </table>
            </div>
        </div>

        <!-- Rapor İndirme (Word + APA) -->
        <div class="glass-panel p-6 rounded-2xl border border-blue-500/20">
            <h3 class="text-blue-400 font-bold text-sm uppercase mb-4">Akademik Rapor İndir</h3>
            <p class="text-[10px] text-slate-400 mb-4">Tüm grafik, tablo, formüller ve APA 7 formatında kaynakça ile Word belgesi oluşturur.</p>
            <button onclick="downloadWordReport()" class="w-full bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 py-3 rounded-xl font-bold text-xs uppercase transition-all border border-blue-500/30">
                📄 Word (APA Kaynakçalı) İndir
            </button>
        </div>

        <!-- Akademik Sonuç -->
        <div class="glass-panel p-8 rounded-2xl border border-indigo-500/30 mt-6">
            <h3 class="text-white font-black text-xl mb-6 uppercase tracking-wider flex items-center gap-3">
                <span class="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-sm italic">Σ</span>
                Bilimsel-Analitik Sonuç
            </h3>
            <div id="conclusion-text" class="space-y-6 text-slate-300 leading-relaxed text-sm md:text-[15px]">
                <p>Yapılan deneysel araştırmalar ve kapsamlı termo-mekanik analizler, yüksek sıcaklığın etkisi altında kayaçların yapısal, mineralojik ve fiziko-mekanik özelliklerinin önemli ölçüde bozulmaya uğradığını göstermektedir. Kütle kaybı (Δm) değerleri, kayaç bünyesindeki higroskopik ve kristal suyun buharlaşması ile karbonat ve diğer termal kararsız minerallerin ayrışmasıyla doğrudan ilişkilidir.</p>
                <p>Analiz sonuçları, Δm'nin sıcaklığa bağımlılığının doğrusal olmayan ve üstel bir karakter sergilediğini, bunun da Arrhenius tipi kinetik süreçlerle yüksek uyum gösterdiğini ortaya koymuştur. Isı transferi süreçleri Fourier yasası ve ısı difüzyon denklemleri çerçevesinde açıklanmakta olup, kayaç içinde düzensiz sıcaklık alanlarının oluşmasına ve buna bağlı olarak yerel gerilme konsantrasyonlarının meydana gelmesine yol açmaktadır.</p>
                <p>Mekanik testler (tek eksenli sıkışma – UCS ve Brezilya çekme dayanımı) kayaç dayanımının artan sıcaklıkla keskin biçimde azaldığını göstermiştir. Bu azalma üstel bozunma modeliyle ifade edilmekte olup, σc(T) fonksiyonundaki düşüş kayaç iç bağ enerjisinin azalması ve mikroçatlak ağının gelişmesiyle açıklanmaktadır.</p>
                <p>Ayrıca yoğunluktaki azalma ve porozitedeki artış, kayaçların genel deformasyon davranışını önemli ölçüde etkilemektedir. Elde edilen sonuçlar Hoek–Brown ve Mohr–Coulomb yenilme ölçütleri çerçevesinde incelendiğinde, kayaç yenilme sınırının sıcaklıkla belirgin biçimde düştüğü saptanmıştır.</p>
                <p>Genel olarak elde edilen bulgular, yeraltı kömür gazlaştırma (UCG) süreçlerinde kayaçların termal bozunma mekanizmalarının derinlemesine anlaşılmasına hizmet etmekte ve gerçek jeoteknik koşullarda duraylılık değerlendirmesi ile güvenliğin sağlanması için önemli bir bilimsel temel oluşturmaktadır.</p>
            </div>
        </div>
    </div>

    <script>
        // ---------- VERİ SETLERİ ----------
        const allDatasets = [
            { label: 'Kireçtaşı UCS-1', data: [{x: 718, y: 25}, {x: 705, y: 100}, {x: 693, y: 500}], baseColor: 0 },
            { label: 'Kireçtaşı UCS-2', data: [{x: 464, y: 25}, {x: 456, y: 100}, {x: 409, y: 1000}], baseColor: 40 },
            { label: 'Kumtaşı UCS-1', data: [{x: 673, y: 25}, {x: 667, y: 100}, {x: 662, y: 500}], baseColor: 210 },
            { label: 'Kumtaşı UCS-2', data: [{x: 701, y: 25}, {x: 694, y: 100}, {x: 667, y: 1000}], baseColor: 260 },
            { label: 'Kireçtaşı Brezilya-1', data: [{x: 197, y: 25}, {x: 191, y: 100}, {x: 174, y: 1000}], baseColor: 150 },
            { label: 'Kireçtaşı Brezilya-2', data: [{x: 196, y: 25}, {x: 193, y: 100}, {x: 191, y: 500}], baseColor: 80 },
            { label: 'Kumtaşı Brezilya-1', data: [{x: 198, y: 25}, {x: 196, y: 100}, {x: 189, y: 1000}], baseColor: 330 },
            { label: 'Kumtaşı Brezilya-2', data: [{x: 193, y: 25}, {x: 193, y: 100}, {x: 191, y: 500}], baseColor: 280 }
        ];

        let currentTab = 'ucs';

        const ctx = document.getElementById('mainChart').getContext('2d');
        const mainChart = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: [] },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: '#1e293b' }, title: { display: true, text: 'Kütle (g)', color: '#94a3b8' } },
                    y: { grid: { color: '#1e293b' }, title: { display: true, text: 'Sıcaklık (°C)', color: '#94a3b8' } }
                },
                plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } }, position: 'bottom' } }
            }
        });

        // ---------- Δm TABLOSU ----------
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
                        const delta = ((m0 - pointT.x) / m0) * 100;
                        cell.innerText = delta.toFixed(2) + '%';
                        cell.style.color = `hsl(0, 80%, ${60 - Math.min(delta/20,1)*20}%)`;
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

        // ---------- SEKMELER ----------
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
            document.querySelectorAll('#checkbox-container input').forEach(cb => {
                if(cb.checked) {
                    const idx = cb.dataset.index;
                    const ds = allDatasets[idx];
                    activeDatasets.push({
                        label: ds.label, data: ds.data, showLine: true,
                        borderColor: `hsl(${ds.baseColor}, 70%, 50%)`,
                        backgroundColor: `hsl(${ds.baseColor}, 70%, 50%, 0.5)`,
                        pointRadius: 6, tension: 0.4
                    });
                }
            });
            mainChart.data.datasets = activeDatasets;
            mainChart.update();
        }

        // ---------- YOĞUNLUK SİMÜLASYONU ----------
        function updateDensitySim() {
            const m = parseFloat(document.getElementById('m-slider').value);
            const v = parseFloat(document.getElementById('v-slider').value);
            const rho = m / v;
            document.getElementById('m-val').innerText = m.toFixed(1) + " kg";
            document.getElementById('v-val').innerText = v.toFixed(1) + " L";
            document.getElementById('rho-display').innerText = rho.toFixed(2) + " kg/L";
            document.getElementById('water-level').style.height = (v / 20 * 100) + "%";
        }

        // ---------- HESAPLAYICILAR ----------
        function calculateDensityExt() {
            const m = parseFloat(document.getElementById('dens-m').value) || 0;
            const v = parseFloat(document.getElementById('dens-v').value) || 0;
            document.getElementById('res-dens').innerText = v>0 ? (m/v).toFixed(3)+" g/cm³" : '-';
        }
        function calculatePorosity() {
            const rb = parseFloat(document.getElementById('rho-b').value) || 0;
            const rs = parseFloat(document.getElementById('rho-s').value) || 0;
            document.getElementById('res-poro').innerText = rs>0 ? ((1 - rb/rs)*100).toFixed(2)+" %" : '-';
        }
        function calculateThermalStrain() {
            const a = parseFloat(document.getElementById('alpha').value)||0, d=parseFloat(document.getElementById('deltaT').value)||0;
            document.getElementById('res-strain').innerText = (a*d).toExponential(3);
        }
        function calculateDegradation() {
            const s = parseFloat(document.getElementById('sig0').value)||0, b=parseFloat(document.getElementById('beta').value)||0, t=parseFloat(document.getElementById('temp').value)||0;
            document.getElementById('res-deg').innerText = (s*Math.exp(-b*t)).toFixed(2)+" MPa";
        }

        // ---------- WORD RAPORU (APA KAYNAKÇALI) ----------
        async function downloadWordReport() {
            const canvas = document.getElementById('mainChart');
            const chartImage = canvas.toDataURL('image/png');
            const tableHtml = document.querySelector('.delta-table').outerHTML;
            const conclusionHtml = document.getElementById('conclusion-text').innerHTML;
            const now = new Date().toLocaleString('tr-TR');
            
            const references = `
                <h3 style="color:#1e293b; margin-top:30px;">Kaynakça (APA 7)</h3>
                <ul style="font-size:12px; color:#334155;">
                    <li>ASTM International. (2020). <i>Standard Test Method for Compressive Strength of Intact Rock Core Specimens</i> (ASTM D7012-14e1).</li>
                    <li>Bieniawski, Z. T. (1989). <i>Engineering Rock Mass Classifications</i>. John Wiley & Sons.</li>
                    <li>Hoek, E., & Brown, E. T. (1997). Practical estimates of rock mass strength. <i>International Journal of Rock Mechanics and Mining Sciences</i>, 34(8), 1165–1186.</li>
                    <li>Jaeger, J. C., Cook, N. G. W., & Zimmerman, R. W. (2007). <i>Fundamentals of Rock Mechanics</i> (4th ed.). Blackwell Publishing.</li>
                    <li>Ulusay, R., & Hudson, J. A. (Eds.). (2007). <i>The Complete ISRM Suggested Methods for Rock Characterization, Testing and Monitoring: 1974–2006</i>. ISRM Turkish National Group.</li>
                    <li>Zhang, L. (2016). <i>Engineering Properties of Rocks</i> (2nd ed.). Butterworth-Heinemann.</li>
                </ul>
            `;
            
            const fullHtml = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Geo-Lab Akademik Rapor - ${now}</title>
                    <style>
                        body { font-family: 'Calibri', sans-serif; margin: 2cm; color: #1e293b; }
                        h1 { color: #1e3a8a; border-bottom: 2px solid #3b82f6; }
                        h2 { color: #334155; margin-top: 30px; }
                        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                        th, td { border: 1px solid #94a3b8; padding: 8px; text-align: center; }
                        th { background: #1e293b; color: white; }
                        img { max-width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <h1>Geo-Lab Jeofizik Analiz Raporu</h1>
                    <p><strong>Oluşturulma Tarihi:</strong> ${now}</p>
                    
                    <h2>1. Kütle – Sıcaklık Grafiği</h2>
                    <img src="${chartImage}" alt="Grafik" />
                    
                    <h2>2. Kütle Kaybı (Δm) Tablosu</h2>
                    ${tableHtml}
                    
                    <h2>3. Temel Formüller</h2>
                    <p>Yoğunluk: ρ = m / V &nbsp;|&nbsp; Porozite: n = (1 - ρb/ρs)·100%</p>
                    <p>Termal deformasyon: ε = α·ΔT &nbsp;|&nbsp; UCS degradasyonu: σ(T) = σ0·e<sup>(-βT)</sup></p>
                    <p>Kütle kaybı: Δm = (m0 - mT) / m0 × 100%</p>
                    
                    <h2>4. Bilimsel Sonuç</h2>
                    <div style="background:#f8fafc; padding:15px; border-left:4px solid #3b82f6;">
                        ${conclusionHtml}
                    </div>
                    
                    ${references}
                    
                    <p style="margin-top:40px; font-size:10px; color:#64748b; text-align:center;">Geo-Lab Jeofizik Laboratuvarı – ${now}</p>
                </body>
                </html>
            `;
            
            const blob = new Blob([fullHtml], { type: 'application/msword' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `GeoLab_Akademik_Rapor_${new Date().toISOString().slice(0,10)}.doc`;
            a.click();
            URL.revokeObjectURL(a.href);
        }

        // ---------- BAŞLAT ----------
        window.onload = () => {
            switchTab('ucs');
            updateDensitySim();
            renderDeltaTable();
        };
    </script>
</body>
</html>
