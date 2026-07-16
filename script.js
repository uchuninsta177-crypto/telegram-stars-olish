const price = 225;

const buttons = document.querySelectorAll(".star-btn");
const total = document.getElementById("totalPrice");
const input = document.getElementById("customStars");
const buyBtn = document.getElementById("buyBtn");
const errorText = document.getElementById("errorText");

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

        checkForm();

        total.innerText = "Jami: " + (stars * price).toLocaleString() + " so'm";
    };
});

input.oninput = () => {

    let stars = parseInt(input.value) || 0;

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

    total.innerText =
        "Jami: " + (stars * price).toLocaleString() + " so'm";

    checkForm();
};


function checkForm() {
    let username = document.getElementById("username").value.trim();
    let stars = Number(input.value);

    if (username !== "" && stars >= 50 && stars <=10000) {
        buyBtn.disabled = false;
        buyBtn.style.opacity = "1";
    } else {
        buyBtn.disabled = true;
        buyBtn.style.opacity = "0.5";
    }

    buyBtn.style.opacity = buyBtn.disabled ? "0.5" : "1";
}

const tg = window.Telegram.WebApp;

document.getElementById("myself").onclick = () => {

    if (tg.initDataUnsafe.user && tg.initDataUnsafe.user.username) {

        document.getElementById("username").value =
            "@" + tg.initDataUnsafe.user.username;

        checkForm();

    } else {

        alert("Username topilmadi!");

    }

};

buyBtn.onclick = async () => {

    let username = document.getElementById("username").value.trim();
    let stars = Number(input.value);
    let totalPrice = stars * price;

    const order = {
        username: username,
        stars: stars,
        total: totalPrice
    };

    try {

        const response = await fetch("https://telegram-stars-olish.onrender.com/order", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(order)
        });

        const result = await response.json();

        alert(result.message);

    } catch (e) {

        alert("Server bilan bog'lanib bo'lmadi!");

    }

};
