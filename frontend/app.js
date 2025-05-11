const nomCarte = "0000";
let key, userId, nx, ny;
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const pixelSize = 30;

async function preinit() {
    const res = await fetch(`/api/v1/${nomCarte}/preinit`);
    const data = await res.json();
    key = data.key;
}

async function init() {
    const res = await fetch(`/api/v1/${nomCarte}/init?key=${key}`, {
        credentials: 'include'
    });
    const data = await res.json();
    userId = data.id;
    nx = data.nx;
    ny = data.ny;
    draw(data.data);
}

function draw(data) {
    for (let x = 0; x < nx; x++) {
        for (let y = 0; y < ny; y++) {
            const [r, g, b] = data[x][y];
            ctx.fillStyle = `rgb(${r},${g},${b})`;
            ctx.fillRect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
        }
    }
}

async function refresh() {
    const res = await fetch(`/api/v1/${nomCarte}/deltas?id=${userId}`, {
        credentials: 'include'
    });
    const data = await res.json();
    data.deltas.forEach(([x, y, r, g, b]) => {
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
    });
}

(async () => {
    await preinit();
    await init();
    setInterval(refresh, 2000); // Update every 2s
})();


const colorPicker = document.getElementById("colorPicker");

canvas.addEventListener("click", async (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) / pixelSize);
    const y = Math.floor((e.clientY - rect.top) / pixelSize);

    const color = colorPicker.value; // e.g., "#ff0000"
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);

    const res = await fetch(`/api/v1/${nomCarte}/edit?x=${x}&y=${y}&r=${r}&g=${g}&b=${b}`, {
        method: "POST",
        credentials: "include"
    });

    const data = await res.json();
    if (data.error) {
        alert(data.error);
    }

    refresh();
});
