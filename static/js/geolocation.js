(() => {
    const button = document.getElementById("get-location");
    const status = document.getElementById("location-status");
    const mapWrapper = document.getElementById("map-wrapper");
    const map = document.getElementById("location-map");
    if (!button || !status) return;

    button.addEventListener("click", () => {
        if (!navigator.geolocation) {
            status.textContent = "Geolocation is not supported by this browser.";
            return;
        }
        button.disabled = true;
        button.textContent = "Pinging...";
        status.textContent = "Contacting child terminal...";

        navigator.geolocation.getCurrentPosition(
            ({ coords }) => {
                const latitude = coords.latitude.toFixed(6);
                const longitude = coords.longitude.toFixed(6);
                status.innerHTML = `Latitude: <strong>${coords.latitude.toFixed(5)}</strong><br>
                    Longitude: <strong>${coords.longitude.toFixed(5)}</strong><br>
                    Accuracy: approximately ${Math.round(coords.accuracy)} metres<br>
                    <a class="font-bold text-fuchsia-400 underline hover:text-fuchsia-300 transition" target="_blank" rel="noopener noreferrer"
                       href="https://www.google.com/maps?q=${latitude},${longitude}">Open full Google Maps</a>`;
                if (map && mapWrapper) {
                    map.src = `https://maps.google.com/maps?q=${latitude},${longitude}&z=16&output=embed`;
                    mapWrapper.classList.remove("hidden");
                }
                button.disabled = false;
                button.textContent = "Re-ping Child";
            },
            (error) => {
                const messages = {
                    1: "Location permission denied by terminal.",
                    2: "Child terminal offline or unable to determine position.",
                    3: "Ping connection timed out.",
                };
                status.textContent = messages[error.code] || "Unable to contact child terminal.";
                mapWrapper?.classList.add("hidden");
                button.disabled = false;
                button.textContent = "Retry Connection";
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
        );
    });
})();
