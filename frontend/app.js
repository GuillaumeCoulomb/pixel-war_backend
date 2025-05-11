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
