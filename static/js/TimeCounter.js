
    document.addEventListener("DOMContentLoaded", function () {
        let timer = 60; // 60 seconds countdown
        const countdownElement = document.getElementById("countdown");

        const interval = setInterval(() => {
            if (timer <= 0) {
                clearInterval(interval);
                countdownElement.innerHTML = "OTP expired. Please resend it.";
                countdownElement.style.color = "red";
            } else {
                timer--;
                countdownElement.innerHTML = `Time left: ${timer} seconds`;
            }
        }, 1000);
    });

