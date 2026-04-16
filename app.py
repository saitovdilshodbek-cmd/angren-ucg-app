<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geo-Lab AI & Ilg'or Geofizika</title>
    <!-- Kutubxonalar -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
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

        .gemini-sparkle { background: linear-gradient(90deg, #4f46e5, #9333ea, #db2777); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold; }
        .ai-loading { animation: pulse 1.5s infinite ease-in-out; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header -->
        <header class="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-6 border border-indigo-500/30 shadow-2xl flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-black tracking-tighter text-white uppercase">Geo-Lab AI ✨</h1>
                <p class="text-indigo-400 text-xs font-bold uppercase tracking-widest mt-1">Sun'iy intellekt bilan quvvatlangan geofizika</p>
            </div>
            <div class="hidden md:block text-right">
                <p class="text-[10px] text-slate-500">LAB STATUS</p>
                <p class="text-green-400 font-mono text-sm">● AI CORE ACTIVE</p>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <!-- Chap panel -->
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

                <!-- AI Tezkor Bashorat -->
                <div class="glass-panel p-5 rounded-2xl border-indigo-500/40">
                    <h3 class="gemini-sparkle text-xs mb-4 uppercase">✨ AI Tezkor Bashorat</h3>
                    <div id="ai-insight-content" class="text-[10px] text-slate-300 italic mb-4 leading-relaxed">
                        Slayderlar orqali zichlikni o'zgartiring va AI tahlilini kuting...
                    </div>
                    <button onclick="getAiInsight()" id="ai-insight-btn" class="w-full bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 py-2 rounded-lg text-[10px] font-bold border border-indigo-500/30 transition-all">✨ Bashoratni yangilash</button>
                </div>
            </div>

            <!-- Asosiy grafik -->
            <div class="lg:col-span-9 space-y-6">
                <div class="glass-panel p-6 rounded-2xl h-[450px] relative">
                    <div class="absolute top-4 left-4 z-10 flex gap-2">
                         <button onclick="analyzeGraphWithGemini()" class="bg-indigo-600 px-4 py-2 rounded-full text-xs font-bold shadow-lg flex items-center gap-2 hover:scale-105 transition-all">
                            ✨ Grafikni tahlil qilish (Gemini)
                         </button>
                         <button onclick="playAiVoice()" id="voice-btn" class="bg-slate-800 px-4 py-2 rounded-full text-xs font-bold border border-slate-700 hidden">
                             🔊 Tinglash
                         </button>
                    </div>
                    <canvas id="mainChart"></canvas>
                </div>

                <!-- Mini galereya -->
                <div class="glass-panel p-4 rounded-xl border-blue-500/20">
                    <h3 class="text-blue-400 font-bold text-[10px] uppercase mb-3">Tanlangan namunalar holati</h3>
                    <div id="sample-gallery" class="grid grid-cols-4 md:grid-cols-8 gap-2"></div>
                </div>
            </div>
        </div>

        <!-- 4 ta geofizik kalkulyator -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
            <div class="glass-panel p-6 rounded-2xl border border-purple-500/20">
                <h3 class="text-purple-400 font-bold text-sm mb-4 uppercase">Zichlik (ρ)</h3>
                <div class="formula-card text-center text-purple-300">ρ = m / V</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="dens-m" placeholder="m (g)" oninput="calculateDensityExt()">
                    <input type="number" id="dens-v" placeholder="V (cm³)" oninput="calculateDensityExt()">
                </div>
                <div class="text-center mt-3 text-purple-300 font-bold" id="res-dens">-</div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border border-yellow-500/20">
                <h3 class="text-yellow-400 font-bold text-sm mb-4 uppercase">Porozlik</h3>
                <div class="formula-card text-center text-yellow-300">n = (1 - ρb/ρs)·100%</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="rho-b" placeholder="ρb" oninput="calculatePorosity()">
                    <input type="number" id="rho-s" placeholder="ρs" oninput="calculatePorosity()">
                </div>
                <div class="text-center mt-3 text-yellow-300 font-bold" id="res-poro">-</div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border border-red-500/20">
                <h3 class="text-red-400 font-bold text-sm mb-4 uppercase">Termal deformatsiya</h3>
                <div class="formula-card text-center text-red-300">ε = α·ΔT</div>
                <div class="grid grid-cols-2 gap-2 text-xs mt-3">
                    <input type="number" id="alpha" placeholder="α" oninput="calculateThermalStrain()">
                    <input type="number" id="deltaT" placeholder="ΔT" oninput="calculateThermalStrain()">
                </div>
                <div class="text-center mt-3 text-red-300 font-bold" id="res-strain">-</div>
            </div>

            <div class="glass-panel p-6 rounded-2xl border border-green-500/20">
                <h3 class="text-green-400 font-bold text-sm mb-4 uppercase">UCS degradatsiyasi</h3>
                <div class="formula-card text-center text-green-300">σ(T)=σ0·e^(-βT)</div>
                <div class="grid grid-cols-3 gap-2 text-xs mt-3">
                    <input type="number" id="sig0" placeholder="σ0" oninput="calculateDegradation()">
                    <input type="number" id="beta" placeholder="β" oninput="calculateDegradation()">
                    <input type="number" id="temp" placeholder="T" oninput="calculateDegradation()">
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
                    $$\Delta m = \frac{m_0 - m_T}{m_0} \times 100\%$$
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
            <p class="text-[10px] text-slate-500 mt-2">* Δm qiymatlari foizda ifodalangan. "-" belgisi ma'lumot mavjud emasligini bildiradi.</p>
        </div>

        <!-- AI bo'limi -->
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
                <h3 class="text-green-400 font-bold text-sm uppercase mb-4">✨ Hisobot</h3>
                <p class="text-[10px] text-slate-400 mb-4">AI tahlili yoki APA manbali Word hujjati yuklab olish.</p>
                <button onclick="generateFullReport()" id="report-gen-btn" class="w-full bg-green-600/20 hover:bg-green-600/40 text-green-400 py-3 rounded-xl font-bold text-xs uppercase transition-all border border-green-500/30 flex items-center justify-center gap-2">
                   ✨ Gemini Hisoboti
                </button>
                <button onclick="downloadWordReport()" class="w-full mt-3 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 py-3 rounded-xl font-bold text-xs uppercase transition-all border border-blue-500/30">
                   📄 APA manbali Word hujjati
                </button>
            </div>
        </div>

        <!-- Ilmiy xulosa -->
        <div class="glass-panel p-8 rounded-2xl border border-indigo-500/30 conclusion-section mt-6">
            <h3 class="text-white font-black text-xl mb-6 uppercase tracking-wider flex items-center gap-3">
                <span class="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-sm italic">Σ</span>
                Ilmiy-analitik xulosa (AI Enhanced)
            </h3>
            <div id="conclusion-text" class="space-y-6 text-slate-300 leading-relaxed text-sm md:text-[15px]">
                <p>Laboratoriya natijalari kutilmoqda. AI tahlilini ishga tushirish uchun "Grafikni tahlil qilish" tugmasini bosing.</p>
            </div>
        </div>
    </div>

    <script>
        // ---------- KONFIGURATSIYA ----------
        // O'zingizning Gemini API kalitingizni kiriting. Bo'sh qoldirsangiz, AI funksiyalari ogohlantirish beradi.
        const apiKey = ""; 
        
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
        let lastAiResponse = "";

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

        // ---------- GEMINI API YORDAMCHI ----------
        async function fetchGemini(prompt, systemPrompt = "Siz professional geofizika muhandisi va laboratoriya mutaxassisiz.") {
            if (!apiKey) {
                alert("Iltimos, kodga o'zingizning Gemini API kalitingizni kiriting.");
                throw new Error("API kaliti mavjud emas");
            }
            const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
            const payload = {
                contents: [{ parts: [{ text: prompt }] }],
                systemInstruction: { parts: [{ text: systemPrompt }] }
            };
            let delay = 1000;
            for (let i = 0; i < 5; i++) {
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    if (!response.ok) throw new Error('API so‘rovi muvaffaqiyatsiz');
                    const result = await response.json();
                    return result.candidates?.[0]?.content?.parts?.[0]?.text;
                } catch (error) {
                    if (i === 4) throw error;
                    await new Promise(resolve => setTimeout(resolve, delay));
                    delay *= 2;
                }
            }
        }

        async function fetchTts(text) {
            if (!apiKey) return;
            const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=${apiKey}`;
            const payload = {
                contents: [{ parts: [{ text: `Say professionally in Uzbek: ${text}` }] }],
                generationConfig: {
                    responseModalities: ["AUDIO"],
                    speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: "Puck" } } }
                }
            };
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                const base64Audio = result.candidates[0].content.parts[0].inlineData.data;
                playWav(base64Audio);
            } catch (error) {
                console.error("TTS xatosi:", error);
            }
        }

        function playWav(base64Data) {
            const binaryString = atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
            
            const wavHeader = new Uint8Array(44);
            const sampleRate = 24000, numChannels = 1, bitsPerSample = 16;
            const blockAlign = numChannels * bitsPerSample / 8;
            const byteRate = sampleRate * blockAlign;
            const dataSize = bytes.length;
            const fileSize = 36 + dataSize;

            const writeString = (offset, str) => { for (let i = 0; i < str.length; i++) wavHeader[offset + i] = str.charCodeAt(i); };
            const writeInt32 = (offset, val) => { const dv = new DataView(wavHeader.buffer); dv.setInt32(offset, val, true); };
            const writeInt16 = (offset, val) => { const dv = new DataView(wavHeader.buffer); dv.setInt16(offset, val, true); };

            writeString(0, 'RIFF'); writeInt32(4, fileSize); writeString(8, 'WAVE');
            writeString(12, 'fmt '); writeInt32(16, 16); writeInt16(20, 1);
            writeInt16(22, numChannels); writeInt32(24, sampleRate); writeInt32(28, byteRate);
            writeInt16(32, blockAlign); writeInt16(34, bitsPerSample); writeString(36, 'data');
            writeInt32(40, dataSize);

            const combined = new Uint8Array(wavHeader.length + bytes.length);
            combined.set(wavHeader);
            combined.set(bytes, wavHeader.length);
            const blob = new Blob([combined], { type: 'audio/wav' });
            new Audio(URL.createObjectURL(blob)).play();
        }

        // ---------- AI FUNKSIYALARI ----------
        async function getAiInsight() {
            const insightEl = document.getElementById('ai-insight-content');
            const btn = document.getElementById('ai-insight-btn');
            const rho = document.getElementById('rho-display').innerText;
            const m = document.getElementById('m-val').innerText;
            const v = document.getElementById('v-val').innerText;
            insightEl.classList.add('ai-loading');
            btn.disabled = true;
            const prompt = `Zichlik simulyatsiyasi ma'lumotlari: Massa=${m}, Hajm=${v}, Zichlik=${rho}. Ushbu zichlikdagi tog' jinsi yuqori haroratda qanday tutishi haqida qisqa ilmiy fikr bildiring.`;
            try {
                const response = await fetchGemini(prompt);
                insightEl.innerText = response;
                lastAiResponse = response;
            } catch (e) {
                insightEl.innerText = "API kaliti mavjud emas yoki xato. Iltimos, tekshiring.";
            } finally {
                insightEl.classList.remove('ai-loading');
                btn.disabled = false;
            }
        }

        async function analyzeGraphWithGemini() {
            const concEl = document.getElementById('conclusion-text');
            concEl.innerHTML = `<div class="ai-loading text-indigo-400">Gemini grafik ma'lumotlarini o'rganmoqda...</div>`;
            const activeData = mainChart.data.datasets.map(d => ({ label: d.label, points: d.data }));
            const prompt = `Laboratoriya natijalari: ${JSON.stringify(activeData)}. Harorat ko'tarilishi bilan massa yo'qotilishi o'rtasidagi bog'liqlikni tahlil qiling va o'zbek tilida kamida 3 paragraf ilmiy xulosa yozing.`;
            try {
                const response = await fetchGemini(prompt);
                concEl.innerHTML = response.split('\n').map(p => p ? `<p>${p}</p>` : '').join('');
                lastAiResponse = response;
                document.getElementById('voice-btn').classList.remove('hidden');
            } catch (e) {
                concEl.innerHTML = `<p class="text-red-400">Tahlil uchun API kaliti kerak. Iltimos, kodga kalitni kiriting.</p>`;
            }
        }

        async function generateFullReport() {
            const btn = document.getElementById('report-gen-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = "Tayyorlanmoqda...";
            btn.disabled = true;
            const prompt = `Laboratoriya natijalari asosida qisqacha hisobot tayyorlang. O'zbek tilida.`;
            try {
                const response = await fetchGemini(prompt);
                const blob = new Blob([response], {type: 'text/plain'});
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = "Gemini_Hisobot.txt";
                a.click();
            } catch (e) {
                alert("Hisobot yaratish uchun API kaliti kerak.");
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }

        function playAiVoice() {
            if (lastAiResponse) fetchTts(lastAiResponse.substring(0, 300));
            else alert("Avval AI tahlilini ishga tushiring.");
        }

        // ---------- WORD EKSPORTI (APA) ----------
        async function downloadWordReport() {
            const canvas = document.getElementById('mainChart');
            const chartImage = canvas.toDataURL('image/png');
            const tableHtml = document.querySelector('.delta-table').outerHTML;
            const conclusionHtml = document.getElementById('conclusion-text').innerHTML;
            const regressionText = document.getElementById('regression-result').innerText;
            const now = new Date().toLocaleString('uz-UZ');
            
            const references = `
                <h3>Adabiyotlar (APA 7)</h3>
                <ul style="font-size:12px;">
                    <li>ASTM D7012-14e1. (2020). Standard Test Method for Compressive Strength of Intact Rock Core Specimens.</li>
                    <li>Hoek, E., & Brown, E. T. (1997). Practical estimates of rock mass strength. <i>Int. J. Rock Mech. Min. Sci.</i>, 34(8), 1165–1186.</li>
                    <li>Ulusay, R., & Hudson, J. A. (2007). <i>The Complete ISRM Suggested Methods for Rock Characterization</i>. ISRM.</li>
                </ul>
            `;
            
            const fullHtml = `
                <!DOCTYPE html>
                <html><head><meta charset="UTF-8"><title>Geo-Lab Hisoboti</title>
                <style>body { font-family: Calibri; margin:2cm; } table { border-collapse: collapse; } th,td { border:1px solid #333; padding:6px; }</style></head>
                <body>
                    <h1>Geo-Lab Analitik Hisoboti</h1>
                    <p><strong>Sana:</strong> ${now}</p>
                    <h2>Grafik</h2>
                    <img src="${chartImage}" style="max-width:100%;">
                    <h2>Massa yo'qotilishi (Δm) jadvali</h2>
                    ${tableHtml}
                    <h2>Regressiya</h2>
                    <p>${regressionText}</p>
                    <h2>Ilmiy xulosa</h2>
                    <div>${conclusionHtml}</div>
                    ${references}
                </body></html>
            `;
            
            const blob = new Blob([fullHtml], { type: 'application/msword' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `GeoLab_Hisobot_${new Date().toISOString().slice(0,10)}.doc`;
            a.click();
        }

        // ---------- Δm jadvali ----------
        function renderDeltaTable() {
            const tbody = document.getElementById('delta-table-body');
            tbody.innerHTML = '';
            allDatasets.forEach(ds => {
                const row = document.createElement('tr');
                const nameCell = document.createElement('td'); nameCell.innerText = ds.label; row.appendChild(nameCell);
                const point25 = ds.data.find(p => p.y === 25);
                const m0 = point25 ? point25.x : null;
                const m0Cell = document.createElement('td'); m0Cell.innerText = m0 ? m0.toFixed(1) : '-'; row.appendChild(m0Cell);
                [100, 500, 1000].forEach(T => {
                    const cell = document.createElement('td');
                    const pointT = ds.data.find(p => p.y === T);
                    if (m0 && pointT) {
                        const delta = ((m0 - pointT.x) / m0) * 100;
                        cell.innerText = delta.toFixed(2) + '%';
                        cell.style.color = `hsl(0, 80%, ${60 - Math.min(delta/20,1)*20}%)`;
                    } else { cell.innerText = '-'; }
                    row.appendChild(cell);
                });
                tbody.appendChild(row);
            });
        }

        // ---------- TAB va FILTR ----------
        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tab-ucs').className = tab === 'ucs' ? "flex-1 py-2 text-[10px] font-bold tab-active" : "flex-1 py-2 text-[10px] font-bold text-slate-500";
            document.getElementById('tab-brazil').className = tab === 'brazil' ? "flex-1 py-2 text-[10px] font-bold tab-active" : "flex-1 py-2 text-[10px] font-bold text-slate-500";
            renderCheckboxes(); updateChartDisplay();
        }

        function renderCheckboxes() {
            const container = document.getElementById('checkbox-container');
            container.innerHTML = '';
            const start = currentTab === 'ucs' ? 0 : 4;
            const end = currentTab === 'ucs' ? 4 : 8;
            for(let i = start; i < end; i++) {
                const div = document.createElement('div');
                div.className = "flex items-center gap-2 p-2 bg-slate-800/30 rounded border border-slate-700 cursor-pointer hover:bg-slate-700/50";
                div.innerHTML = `<input type="checkbox" checked onchange="updateChartDisplay()" data-index="${i}" class="w-3 h-3 accent-indigo-500"><span class="text-[10px] text-slate-300">${allDatasets[i].label}</span>`;
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
            calculateRegression();
        }

        // ---------- ZICHLIK ----------
        function updateDensitySim() {
            const m = parseFloat(document.getElementById('m-slider').value);
            const v = parseFloat(document.getElementById('v-slider').value);
            const rho = m / v;
            document.getElementById('m-val').innerText = m.toFixed(1) + " kg";
            document.getElementById('v-val').innerText = v.toFixed(1) + " L";
            document.getElementById('rho-display').innerText = rho.toFixed(2) + " kg/L";
            document.getElementById('water-level').style.height = (v / 20 * 100) + "%";
        }

        // ---------- KALKULYATORLAR ----------
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

        // ---------- REGRESSIYA & NN ----------
        function calculateRegression() {
            let x=[], y=[];
            allDatasets.slice(0,4).forEach(ds => {
                const m0 = ds.data[0].x;
                ds.data.forEach(p => { if(p.y!==25) { let dm=((m0-p.x)/m0)*100; x.push(dm); y.push(100-dm*5); } });
            });
            if(x.length<2) return;
            let n=x.length, sx=x.reduce((a,b)=>a+b), sy=y.reduce((a,b)=>a+b);
            let sxy=x.reduce((a,b,i)=>a+b*y[i],0), sxx=x.reduce((a,b)=>a+b*b);
            let slope=(n*sxy-sx*sy)/(n*sxx-sx*sx), intercept=(sy-slope*sx)/n;
            document.getElementById("regression-result").innerText = `σc = ${intercept.toFixed(2)} - ${Math.abs(slope).toFixed(2)}·Δm`;
        }

        async function trainModel() {
            let x=[], y=[];
            allDatasets.slice(0,4).forEach(ds => {
                const m0 = ds.data[0].x;
                ds.data.forEach(p => { if(p.y!==25) { let dm=((m0-p.x)/m0)*100; x.push(dm); y.push(100-dm*5); } });
            });
            const xs = tf.tensor2d(x, [x.length,1]), ys = tf.tensor2d(y, [y.length,1]);
            nnModel = tf.sequential();
            nnModel.add(tf.layers.dense({units:8, inputShape:[1], activation:'relu'}));
            nnModel.add(tf.layers.dense({units:1}));
            nnModel.compile({optimizer: tf.train.adam(0.01), loss:'meanSquaredError'});
            await nnModel.fit(xs, ys, {epochs:50});
            document.getElementById('ai-status').innerText = "Model tayyor ✅";
        }

        async function predictWithNN() {
            if(!nnModel) { document.getElementById('prediction-result').innerText = "Avval o'rgating"; return; }
            const t = parseFloat(document.getElementById('predict-temp').value)||0;
            let dm = t*0.08;
            const pred = nnModel.predict(tf.tensor2d([dm],[1,1]));
            const val = (await pred.data())[0];
            document.getElementById('prediction-result').innerText = val.toFixed(2)+" MPa";
        }

        // ---------- START ----------
        window.onload = () => {
            switchTab('ucs');
            updateDensitySim();
            renderDeltaTable();
        };
    </script>
</body>
</html>
import streamlit as st

st.set_page_config(layout="wide", page_title="Geo-Lab AI")
st.title("Geo-Lab AI Dashboard")

# HTML faylni o'qib, brauzerda ko'rsatamiz
with open("index.html", "r", encoding="utf-8") as f:
    html_code = f.read()

st.components.v1.html(html_code, height=1200, scrolling=True)
