const price = 225;

// URL parametridan 'balance' qiymatini o'qib olamiz
const urlParams = new URLSearchParams(window.location.search);
const userBalance = parseInt(urlParams.get('balance'), 10) || 0;

const buttons = document.querySelectorAll(".star-btn");
const total = document.getElementById("totalPrice");
const input = document.getElementById("customStars");
const buyBtn = document.getElementById("buyBtn");
const errorText = document.getElementById("errorText");
const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
    tg.ready();
    tg.expand();
}

buyBtn.disabled = true;
buyBtn.style.opacity = "0.5";

document.getElementById("username").oninput = checkForm;

buttons.forEach(btn => {
    btn.onclick = () => {
        let stars = Number(btn.innerText);

        input.value = stars;
        input.style.color = "white";

        errorText.style.display = "none";
        errorText.innerText = "";

        total.innerText = "Jami: " + (stars * price).toLocaleString() + " so'm";

        checkForm();
    };
});

input.oninput = () => {
    let stars = parseInt(input.value, 10) || 0;

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
    }

    total.innerText = "Jami: " + (stars * price).toLocaleString() + " so'm";

    checkForm();
};

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
            errorText.style.display = "none";
            buyBtn.disabled = false;
            buyBtn.style.opacity = "1";
        }
    } else {
        buyBtn.disabled = true;
        buyBtn.style.opacity = "0.5";
    }
}

document.getElementById("myself").onclick = () => {
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const u = tg.initDataUnsafe.user;
        document.getElementById("username").value = u.username ? "@" + u.username : "ID:" + u.id;
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
        alert("Balansingizda mablag' yetarli emas! Iltimos, balansingizni to'ldiring.");
        return;
    }

    // Ikki marta bosib yubormaslik uchun tugmani muzlatamiz
    buyBtn.disabled = true;
    buyBtn.innerText = "Yuborilmoqda...";
    buyBtn.style.opacity = "0.5";

    const order = {
        user_id: userId,
        username: username,
        stars: stars,
        total: totalPrice
    };

    // 5 soniyalik timeout bilan fetch
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
        const response = await fetch("https://telegram-stars-olish.onrender.com/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(order),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const result = await response.json();

        if (result.success) {
            alert(result.message || "✅ Buyurtma qabul qilindi!");
            sendAndClose(order);
        } else {
            alert("❌ Xatolik: " + (result.message || "Buyurtma yuborilmadi."));
            resetBuyButton();
        }
    } catch (e) {
        clearTimeout(timeoutId);
        // Server kechiksa yoki o'chiq bo'lsa ham botga ma'lumot uzatamiz
        if (tg && tg.sendData) {
            sendAndClose(order);
        } else {
            alert("❌ Server bilan bog'lanishda xatolik yuz berdi!");
            resetBuyButton();
        }
    }
};

function sendAndClose(orderData) {
    if (tg && tg.sendData) {
        tg.sendData(JSON.stringify(orderData));
    }
    if (tg && tg.close) {
        tg.close();
    }
}

function resetBuyButton() {
    buyBtn.disabled = false;
    buyBtn.innerText = "Sotib olish";
    buyBtn.style.opacity = "1";
}
