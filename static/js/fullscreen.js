(() => {
    const button = document.getElementById("open-fullscreen");
    const panel = document.getElementById("dashboard-panel");
    const status = document.getElementById("fullscreen-status");
    if (!button || !panel || !status) return;

    button.addEventListener("click", async () => {
        try {
            if (!document.fullscreenElement) {
                if (!panel.requestFullscreen) {
                    status.textContent = "Fullscreen is not supported by this browser.";
                    return;
                }
                await panel.requestFullscreen();
            } else {
                await document.exitFullscreen();
            }
        } catch {
            status.textContent = "The fullscreen request could not be completed.";
        }
    });

    document.addEventListener("fullscreenchange", () => {
        const isFullscreen = Boolean(document.fullscreenElement);
        button.textContent = isFullscreen ? "Exit fullscreen" : "Open fullscreen";
        status.textContent = isFullscreen
            ? "Fullscreen dashboard is active."
            : "Standard view is active.";
    });
})();
