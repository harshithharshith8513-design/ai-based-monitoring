(() => {
    const alertButton = document.getElementById("send-alert");
    const alertStatus = document.getElementById("notification-status");
    const alertType = document.getElementById("notification-type");
    const customAlertWrap = document.getElementById("custom-notification-wrap");
    const customAlert = document.getElementById("custom-notification");
    const alarmButton = document.getElementById("play-alarm");
    const alarmStatus = document.getElementById("alarm-status");
    let audioContext = null;
    let alarmTimer = null;

    alertType?.addEventListener("change", () => {
        customAlertWrap?.classList.toggle("hidden", alertType.value !== "custom");
        if (alertType.value === "custom") customAlert?.focus();
    });

    alertButton?.addEventListener("click", async () => {
        if (!("Notification" in window)) {
            alertStatus.textContent = "Notifications are not supported by this browser.";
            return;
        }
        try {
            const permission = Notification.permission === "default"
                ? await Notification.requestPermission()
                : Notification.permission;
            if (permission !== "granted") {
                alertStatus.textContent = "Notification permission was not granted.";
                return;
            }
            const message = alertType?.value === "custom"
                ? customAlert?.value.trim()
                : alertType?.value;
            if (!message) {
                alertStatus.textContent = "Enter a custom notification message first.";
                customAlert?.focus();
                return;
            }
            new Notification("ChildGuard AI parent alert", {
                body: message,
                tag: `childguard-${Date.now()}`,
            });
            alertStatus.textContent = `Notification sent: ${message}`;
        } catch {
            alertStatus.textContent = "The notification could not be sent.";
        }
    });

    function playTone() {
        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();
        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(740, audioContext.currentTime);
        gain.gain.setValueAtTime(.0001, audioContext.currentTime);
        gain.gain.exponentialRampToValueAtTime(.22, audioContext.currentTime + .03);
        gain.gain.exponentialRampToValueAtTime(.0001, audioContext.currentTime + .35);
        oscillator.connect(gain).connect(audioContext.destination);
        oscillator.start();
        oscillator.stop(audioContext.currentTime + .36);
    }

    function stopAlarm() {
        window.clearInterval(alarmTimer);
        alarmTimer = null;
        alarmButton.textContent = "Play alarm";
        alarmStatus.textContent = "Alarm is stopped.";
    }

    alarmButton?.addEventListener("click", async () => {
        if (alarmTimer) {
            stopAlarm();
            return;
        }
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) {
            alarmStatus.textContent = "Web Audio is not supported by this browser.";
            return;
        }
        audioContext ??= new AudioContext();
        if (audioContext.state === "suspended") await audioContext.resume();
        playTone();
        alarmTimer = window.setInterval(playTone, 700);
        alarmButton.textContent = "Stop alarm";
        alarmStatus.textContent = "Audible alarm is playing.";
    });

    window.addEventListener("pagehide", () => {
        if (alarmTimer) stopAlarm();
        audioContext?.close();
    });
})();
