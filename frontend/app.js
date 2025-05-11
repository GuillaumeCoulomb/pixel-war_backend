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
