const price = 225;

const urlParams = new URLSearchParams(window.location.search);
const userBalance = parseInt(urlParams.get('balance')) || 0;

const buttons = document.querySelectorAll(".star-btn");
const total = document.getElementById("totalPrice");
const input = document.getElementById("customStars");
const buyBtn = document.getElementById("buyBtn");
const errorText = document.getElementById("errorText");

buyBtn.disabled = true;
buyBtn.style.opacity = "0.5";

document.getElementById("username").oninput = checkForm;

// Tezkor tugmalar
buttons.forEach(btn => {
    btn.onclick = () => {
        let stars = Number(btn.innerText);
        input.value = stars;
        validateStars(stars);
        checkForm();
    };
});

// Qo'lda kiritish
input.oninput = () => {
    let stars = parseInt(input.value) || 0;
    validateStars(stars);
    checkForm();
};

function validateStars(stars) {
    if (stars < 50) {
        input.style.color = "#ff4d4d";
        errorText.style.display = "block";
        errorText.innerText = "❌ Minimum 50 Stars kiriting";
    } else if (stars > 10000) {
        input.style.color = "#ff4d4d";
        errorText.style.display = "block";
        errorText.innerText = "❌ Maksimum 10000 Stars mumkin";
    } else {
        input.style.color = "white";
        errorText.style.display = "none";
        errorText.innerText = "";
    }
    total.innerText = "Jami: " + (stars * price).toLocaleString() + " so'm";
}

function checkForm() {
    let username = document.getElementById("username").value.trim();
    let stars = Number(input.value);
    let totalPrice = stars * price;

    if (username !== "" && stars >= 50 && stars <= 10000) {
        if (totalPrice > userBalance) {
            errorText.style.display = "block";
            errorText.innerText = "❌ Balansingizda mablag' yetarli emas!";
            buyBtn.disabled = true;
            buyBtn.style.opacity = "0.5";
        } else {
            buyBtn.disabled = false;
            buyBtn.style.opacity = "1";
        }
    } else {
        buyBtn.disabled = true;
        buyBtn.style.opacity = "0.5";
    }
}

const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
    tg.ready();
    tg.expand();
}

document.getElementById("myself").onclick = () => {
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.username) {
        document.getElementById("username").value = "@" + tg.initDataUnsafe.user.username;
        checkForm();
    } else {
        alert("Username topilmadi!");
    }
};

buyBtn.onclick = async () => {
    let username = document.getElementById("username").value.trim();
    let stars = Number(input.value);
    let totalPrice = stars * price;
    let userId = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user.id : null;

    if (totalPrice > userBalance) {
        alert("Balansingizda mablag' yetarli emas!");
        return;
    }

    const order = {
        user_id: userId,
        username: username,
        stars: stars,
        total: totalPrice
    };

    if (tg && tg.sendData) {
        try {
            tg.sendData(JSON.stringify(order));
            tg.close();
        } catch (e) {
            alert("Xatolik yuz berdi: " + e.message);
        }
    } else {
        alert("Ushbu tugma faqat Telegram ilovasi ichida ishlaydi!");
    }
};
