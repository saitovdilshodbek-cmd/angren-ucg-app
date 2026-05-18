// ===========================
// ADVANCED SCIENTIFIC UCG ENGINE
// ===========================

// Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050508);
scene.fog = new THREE.FogExp2(0x050508, 0.0025);

// Camera
const camera = new THREE.PerspectiveCamera(
    50,
    container.clientWidth/container.clientHeight,
    0.1,
    5000
);

camera.position.set(250,180,420);

// Renderer
const renderer = new THREE.WebGLRenderer({
    antialias:true,
    powerPreference:"high-performance"
});

renderer.setSize(container.clientWidth, container.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

container.appendChild(renderer.domElement);

// Controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;

// ===========================
// LIGHTING SYSTEM
// ===========================

const hemi = new THREE.HemisphereLight(0x88aaff,0x111111,0.5);
scene.add(hemi);

const dirLight = new THREE.DirectionalLight(0xffffff,1.2);
dirLight.position.set(200,300,100);

dirLight.castShadow = true;

dirLight.shadow.mapSize.width = 4096;
dirLight.shadow.mapSize.height = 4096;

scene.add(dirLight);

// Underground combustion light
const combustionLight = new THREE.PointLight(0xff5500,4,800);
scene.add(combustionLight);

// ===========================
// GEOLOGICAL STRATA
// ===========================

const strataGroup = new THREE.Group();
scene.add(strataGroup);

function createLayer(y, thickness, color, roughness){

    const geo = new THREE.BoxGeometry(900, thickness, 300);

    const mat = new THREE.MeshStandardMaterial({
        color: color,
        roughness: roughness,
        metalness:0.02
    });

    const mesh = new THREE.Mesh(geo,mat);

    mesh.position.y = y;

    mesh.receiveShadow = true;
    mesh.castShadow = true;

    strataGroup.add(mesh);

    return mesh;
}

// Overburden
createLayer(-20,40,0x6b7280,0.95);

// Sandstone
createLayer(-70,50,0xc2b280,0.9);

// Shale
createLayer(-130,45,0x444444,0.95);

// Coal seam
const coalLayer = createLayer(-190,30,0x111111,0.8);

// Basement rock
createLayer(-250,100,0x555555,1.0);

// ===========================
// SURFACE TERRAIN
// ===========================

const terrainRes = 180;

const terrainGeo = new THREE.PlaneGeometry(
    900,
    900,
    terrainRes,
    terrainRes
);

terrainGeo.rotateX(-Math.PI/2);

const terrainMat = new THREE.MeshStandardMaterial({
    color:0x2a3b2f,
    roughness:1,
    metalness:0
});

const terrain = new THREE.Mesh(terrainGeo, terrainMat);

terrain.receiveShadow = true;
terrain.castShadow = false;

scene.add(terrain);

// Initial terrain noise
const pos = terrain.geometry.attributes.position;

for(let i=0;i<pos.count;i++){

    const x = pos.getX(i);
    const z = pos.getZ(i);

    const noise =
        Math.sin(x*0.015)*2 +
        Math.cos(z*0.018)*2 +
        Math.sin((x+z)*0.01)*1.5;

    pos.setY(i, noise);
}

terrain.geometry.computeVertexNormals();

// ===========================
// REALISTIC CRIP CHANNEL
// ===========================

const cavityGroup = new THREE.Group();
scene.add(cavityGroup);

const cavityPath = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-70,-190,0),
    new THREE.Vector3(-20,-192,5),
    new THREE.Vector3(40,-188,-4),
    new THREE.Vector3(90,-190,3)
]);

const cavityGeo = new THREE.TubeGeometry(
    cavityPath,
    120,
    state.R,
    32,
    false
);

// Thermal shader
const cavityMat = new THREE.MeshPhysicalMaterial({
    color:0xff6600,
    emissive:0xff3300,
    emissiveIntensity:3,
    roughness:0.2,
    transmission:0.05,
    thickness:1.5
});

const cavityMesh = new THREE.Mesh(cavityGeo,cavityMat);

cavityMesh.castShadow = true;

cavityGroup.add(cavityMesh);

// ===========================
// THERMAL PLUME
// ===========================

const plumeGeo = new THREE.SphereGeometry(45,64,64);

const plumeMat = new THREE.MeshBasicMaterial({
    color:0xff4400,
    transparent:true,
    opacity:0.08
});

const plume = new THREE.Mesh(plumeGeo,plumeMat);

plume.position.set(0,-190,0);

scene.add(plume);

// ===========================
// FRACTURE NETWORK
// ===========================

const fractureGroup = new THREE.Group();
scene.add(fractureGroup);

for(let i=0;i<120;i++){

    const points = [];

    const sx = (Math.random()-0.5)*180;
    const sy = -190 + (Math.random()-0.5)*40;
    const sz = (Math.random()-0.5)*90;

    points.push(new THREE.Vector3(sx,sy,sz));

    points.push(new THREE.Vector3(
        sx + (Math.random()-0.5)*30,
        sy + (Math.random()-0.5)*20,
        sz + (Math.random()-0.5)*30
    ));

    const geo = new THREE.BufferGeometry().setFromPoints(points);

    const mat = new THREE.LineBasicMaterial({
        color:0xffaa33,
        transparent:true,
        opacity:0.25
    });

    const line = new THREE.Line(geo,mat);

    fractureGroup.add(line);
}

// ===========================
// WELLS
// ===========================

function makeWell(x,color){

    const geo = new THREE.CylinderGeometry(2,2,220,16);

    const mat = new THREE.MeshStandardMaterial({
        color:color,
        emissive:color,
        emissiveIntensity:0.4,
        metalness:0.7,
        roughness:0.3
    });

    const well = new THREE.Mesh(geo,mat);

    well.position.set(x,-95,0);

    well.castShadow = true;

    scene.add(well);

    return well;
}

const injWell = makeWell(-90,0x3b82f6);
const prodWell = makeWell(90,0xfbbf24);

// ===========================
// SUBSIDENCE MODEL
// ===========================

function updateSubsidence(){

    const positions = terrain.geometry.attributes.position;

    for(let i=0;i<positions.count;i++){

        const x = positions.getX(i);
        const z = positions.getZ(i);

        const r = Math.sqrt(x*x + z*z);

        // Realistic subsidence bowl
        const subs =
            Math.exp(-(r*r)/(2*140*140))
            * state.R
            * 2.5;

        const tectonic =
            Math.sin(x*0.01)*0.8 +
            Math.cos(z*0.008)*0.6;

        positions.setY(i,-subs + tectonic);
    }

    positions.needsUpdate = true;

    terrain.geometry.computeVertexNormals();
}

// ===========================
// TEMPERATURE RESPONSE
// ===========================

function updateTemperature(){

    const tNorm = (state.T - 300)/900;

    cavityMat.emissiveIntensity = 2 + tNorm*6;

    plume.scale.setScalar(1 + tNorm*1.5);

    combustionLight.intensity = 3 + tNorm*6;

    combustionLight.position.set(0,-180,0);

    fractureGroup.children.forEach(f=>{

        f.material.opacity = 0.08 + tNorm*0.35;
    });
}

// ===========================
// STRESS FIELD VISUALIZATION
// ===========================

const stressGeo = new THREE.RingGeometry(50,52,64);

const stressMat = new THREE.MeshBasicMaterial({
    color:0xff0000,
    transparent:true,
    opacity:0.15,
    side:THREE.DoubleSide
});

const stressRing = new THREE.Mesh(stressGeo,stressMat);

stressRing.rotation.x = -Math.PI/2;
stressRing.position.y = -188;

scene.add(stressRing);

// ===========================
// ANIMATION
// ===========================

function animate(){

    requestAnimationFrame(animate);

    controls.update();

    const t = Date.now()*0.001;

    // Thermal pulsation
    cavityMesh.scale.y =
        1 + Math.sin(t*4)*0.03;

    plume.material.opacity =
        0.05 + Math.sin(t*2)*0.02;

    stressRing.scale.setScalar(
        1 + Math.sin(t*3)*0.04
    );

    renderer.render(scene,camera);
}

updateSubsidence();
updateTemperature();
animate();

// ===========================
// RESIZE
// ===========================

window.addEventListener('resize',()=>{

    camera.aspect =
        container.clientWidth/container.clientHeight;

    camera.updateProjectionMatrix();

    renderer.setSize(
        container.clientWidth,
        container.clientHeight
    );
});
