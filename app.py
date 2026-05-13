import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.ndimage import gaussian_filter
from scipy.optimize import minimize
from scipy.stats import linregress, norm as gaussian_dist
import time
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
import io
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import sys
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve, r2_score
from sklearn.model_selection import KFold
import joblib
from sklearn.preprocessing import StandardScaler
import requests
import logging
from scipy.signal import savgol_filter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    PT_AVAILABLE = True
    device = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    PT_AVAILABLE = False
    device = "cpu"

try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

try:
    from pyDOE import lhs
    PYDOE_AVAILABLE = True
except ImportError:
    PYDOE_AVAILABLE = False

try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    from filterpy.kalman import KalmanFilter
    FILTERPY_AVAILABLE = True
except ImportError:
    FILTERPY_AVAILABLE = False

try:
    import pymc as pm
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False

try:
    import torch_geometric.nn as geo_nn
    TORCH_GEO_AVAILABLE = True
except ImportError:
    TORCH_GEO_AVAILABLE = False

try:
    import cupy as cp
    GPU_AVAILABLE = True
    xp = cp
except ImportError:
    GPU_AVAILABLE = False
    xp = np

try:
    from mpi4py import MPI
    MPI_AVAILABLE = True
except ImportError:
    MPI_AVAILABLE = False

# -------------------------------------------------------------------
# Tarjimalar va barcha funksiyalar (avvalgi kod o‘z holida qoldirilgan)
# -------------------------------------------------------------------
# ... (avvalgi barcha TRANSLATIONS, yordamchi funksiyalar, klasslar va hisoblashlar) 
# [Eslatma: Kodning to‘liq ko‘rinishi uchun quyida faqat o‘zgartirilgan qism ko‘rsatilgan,
#  lekin siz skriptning qolgan qismini o‘z joyida qoldirasiz]

# -------------------------------------------------------------------
# Asl Streamlit ilovasining oxirgi qismiga quyidagi kodni qo‘shing
# -------------------------------------------------------------------

# ---- IDEAL GAZ SIMULYATSIYASI (HTML/JS) ----
ideal_gas_html = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ideal Gaz Qonuni Simulyatsiyasi</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #121212;
            color: #e0e0e0;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        .glass-panel {
            background: rgba(30, 30, 30, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        input[type=range] {
            accent-color: #4f46e5;
        }
        canvas {
            border-radius: 1rem;
        }
    </style>
</head>
<body>

<div class="max-w-5xl w-full p-4">
    <div class="glass-panel rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row h-[600px]">
        
        <!-- Left Panel: Controls -->
        <div class="w-full md:w-1/2 p-8 flex flex-col justify-between border-b md:border-b-0 md:border-r border-white/10">
            <div class="flex justify-between items-center mb-4">
                <button class="text-white/50 hover:text-white transition">✕</button>
                <div class="flex gap-4">
                    <button class="text-white/50 hover:text-white transition">↺</button>
                    <button class="text-white/50 hover:text-white transition">📋</button>
                    <button class="text-white/50 hover:text-white transition">👍</button>
                </div>
            </div>

            <!-- Equation Display -->
            <div class="text-center my-8">
                <h2 id="equation-display" class="text-4xl italic font-light tracking-widest text-white">
                    P = nRT / V
                </h2>
            </div>

            <!-- Sliders -->
            <div class="space-y-6">
                <!-- Pressure P -->
                <div class="flex items-center gap-4">
                    <span class="w-4 font-bold italic">P</span>
                    <span id="p-val" class="w-12 text-sm">8.56</span>
                    <input type="range" id="p-slider" min="0.1" max="20" step="0.1" class="flex-grow h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer">
                    <input type="radio" name="solve-for" value="P" checked class="w-4 h-4 cursor-pointer">
                </div>
                <!-- Volume V -->
                <div class="flex items-center gap-4">
                    <span class="w-4 font-bold italic">V</span>
                    <span id="v-val" class="w-12 text-sm">4.0</span>
                    <input type="range" id="v-slider" min="1" max="10" step="0.1" class="flex-grow h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer">
                    <input type="radio" name="solve-for" value="V" class="w-4 h-4 cursor-pointer">
                </div>
                <!-- Moles n -->
                <div class="flex items-center gap-4">
                    <span class="w-4 font-bold italic">n</span>
                    <span id="n-val" class="w-12 text-sm">1.40</span>
                    <input type="range" id="n-slider" min="0.1" max="5" step="0.05" class="flex-grow h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer">
                    <input type="radio" name="solve-for" value="n" class="w-4 h-4 cursor-pointer">
                </div>
                <!-- Temperature T -->
                <div class="flex items-center gap-4">
                    <span class="w-4 font-bold italic">T</span>
                    <span id="t-val" class="w-12 text-sm">298.0</span>
                    <input type="range" id="t-slider" min="100" max="600" step="1" class="flex-grow h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer">
                    <input type="radio" name="solve-for" value="T" class="w-4 h-4 cursor-pointer">
                </div>
            </div>
        </div>

        <!-- Right Panel: 3D Visualization -->
        <div id="canvas-container" class="w-full md:w-1/2 relative bg-neutral-900 flex items-center justify-center p-4">
            <!-- Three.js will inject canvas here -->
        </div>
    </div>
</div>

<script>
const R = 0.0821; // Gas constant
let state = {
    P: 8.56,
    V: 4.0,
    n: 1.4,
    T: 298.0,
    solveFor: 'P'
};

const sliders = {
    P: document.getElementById('p-slider'),
    V: document.getElementById('v-slider'),
    n: document.getElementById('n-slider'),
    T: document.getElementById('t-slider')
};

const displays = {
    P: document.getElementById('p-val'),
    V: document.getElementById('v-val'),
    n: document.getElementById('n-val'),
    T: document.getElementById('t-val'),
    equation: document.getElementById('equation-display')
};

const radios = document.querySelectorAll('input[name="solve-for"]');

function updateMath(changedKey) {
    if (state.solveFor === 'P') {
        state.P = (state.n * R * state.T) / state.V;
    } else if (state.solveFor === 'V') {
        state.V = (state.n * R * state.T) / state.P;
    } else if (state.solveFor === 'n') {
        state.n = (state.P * state.V) / (R * state.T);
    } else if (state.solveFor === 'T') {
        state.T = (state.P * state.V) / (state.n * R);
    }
    syncUI();
}

function syncUI() {
    for (let key in sliders) {
        sliders[key].value = state[key];
        displays[key].innerText = state[key].toFixed(2);
        // Disable the slider that is being solved for
        sliders[key].disabled = (key === state.solveFor);
        sliders[key].style.opacity = (key === state.solveFor) ? "0.3" : "1";
    }

    // Update equation text
    const eqs = {
        P: "P = nRT / V",
        V: "V = nRT / P",
        n: "n = PV / RT",
        T: "T = PV / nR"
    };
    displays.equation.innerText = eqs[state.solveFor];
}

// Event Listeners
Object.keys(sliders).forEach(key => {
    sliders[key].addEventListener('input', (e) => {
        state[key] = parseFloat(e.target.value);
        updateMath(key);
    });
});

radios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        state.solveFor = e.target.value;
        updateMath();
    });
});

const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);
const pointLight = new THREE.PointLight(0xffffff, 0.8);
pointLight.position.set(5, 5, 5);
scene.add(pointLight);

// Cylinder Geometry
const cylinderGeom = new THREE.CylinderGeometry(2, 2, 8, 32, 1, true);
const cylinderMat = new THREE.MeshPhongMaterial({ 
    color: 0x444444, 
    transparent: true, 
    opacity: 0.3, 
    side: THREE.DoubleSide 
});
const cylinder = new THREE.Mesh(cylinderGeom, cylinderMat);
scene.add(cylinder);

// Piston
const pistonGeom = new THREE.CylinderGeometry(2, 2, 0.2, 32);
const pistonMat = new THREE.MeshPhongMaterial({ color: 0x666666 });
const piston = new THREE.Mesh(pistonGeom, pistonMat);
scene.add(piston);

// Base
const baseGeom = new THREE.CylinderGeometry(2.05, 2.05, 0.2, 32);
const baseMat = new THREE.MeshPhongMaterial({ color: 0x333333 });
const base = new THREE.Mesh(baseGeom, baseMat);
base.position.y = -4;
scene.add(base);

const particlesCount = 100;
const particleGeometry = new THREE.SphereGeometry(0.06, 8, 8);
const particleMaterial = new THREE.MeshBasicMaterial({ color: 0x60a5fa });
const particles = [];

for (let i = 0; i < particlesCount; i++) {
    const p = new THREE.Mesh(particleGeometry, particleMaterial);
    p.position.set(
        (Math.random() - 0.5) * 3.5,
        (Math.random() - 0.5) * 4 - 2,
        (Math.random() - 0.5) * 3.5
    );
    p.velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 0.1,
        (Math.random() - 0.5) * 0.1,
        (Math.random() - 0.5) * 0.1
    );
    particles.push(p);
    scene.add(p);
}

camera.position.z = 12;
camera.position.y = 2;
camera.lookAt(0, 0, 0);

function animate() {
    requestAnimationFrame(animate);

    // V mapped to piston height
    const targetHeight = (state.V / 10) * 8 - 4;
    piston.position.y = THREE.MathUtils.lerp(piston.position.y, targetHeight, 0.1);

    // Particle movement speed based on T
    const speedFactor = state.T / 300;

    particles.forEach((p, index) => {
        const visibleLimit = (state.n / 5) * particlesCount;
        p.visible = index < visibleLimit;

        if (p.visible) {
            p.position.add(p.velocity.clone().multiplyScalar(speedFactor));

            // Boundaries
            const radius = 1.9;
            const dist = Math.sqrt(p.position.x**2 + p.position.z**2);
            
            if (dist > radius) {
                const normal = new THREE.Vector3(p.position.x, 0, p.position.z).normalize();
                p.velocity.reflect(normal);
                p.position.x = normal.x * radius;
                p.position.z = normal.z * radius;
            }

            if (p.position.y < -3.9) {
                p.velocity.y *= -1;
                p.position.y = -3.9;
            }

            if (p.position.y > piston.position.y - 0.1) {
                p.velocity.y *= -1;
                p.position.y = piston.position.y - 0.1;
            }
        }
    });

    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});

window.onload = () => {
    syncUI();
    animate();
};
</script>
</body>
</html>
"""

with st.expander("🧪 Ideal gaz qonuni simulyatsiyasi (3D)"):
    st.components.v1.html(ideal_gas_html, height=650)
    st.caption("Ideal gaz holat tenglamasi: PV = nRT. P, V, n, T parametrlarini slayderlar yoki radio tugmalar yordamida tanlang.")
