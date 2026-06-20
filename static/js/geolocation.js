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
        button.textContent = "Locating...";
        status.textContent = "Waiting for location permission...";

        navigator.geolocation.getCurrentPosition(
            ({ coords }) => {
                const latitude = coords.latitude.toFixed(6);
                const longitude = coords.longitude.toFixed(6);
                status.innerHTML = `Latitude: <strong>${coords.latitude.toFixed(5)}</strong><br>
                    Longitude: <strong>${coords.longitude.toFixed(5)}</strong><br>
                    Accuracy: approximately ${Math.round(coords.accuracy)} metres<br>
                    <a class="font-bold text-blue-700 underline" target="_blank" rel="noopener noreferrer"
                       href="https://www.google.com/maps?q=${latitude},${longitude}">Open full Google Maps</a>`;
                if (map && mapWrapper) {
                    map.src = `https://maps.google.com/maps?q=${latitude},${longitude}&z=16&output=embed`;
                    mapWrapper.classList.remove("hidden");
                }
                button.disabled = false;
                button.textContent = "Refresh location";
            },
            (error) => {
                const messages = {
                    1: "Location permission was denied.",
                    2: "The device could not determine its location.",
                    3: "The location request timed out.",
                };
                status.textContent = messages[error.code] || "Unable to retrieve location.";
                mapWrapper?.classList.add("hidden");
                button.disabled = false;
                button.textContent = "Try again";
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
        );
    });
})();
