(() => {
    const input = document.getElementById("child-photo");
    const preview = document.getElementById("photo-preview");
    const placeholder = document.getElementById("photo-placeholder");
    const status = document.getElementById("file-status");
    if (!input || !preview || !placeholder || !status) return;

    const allowedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
    const maxSize = 2 * 1024 * 1024;

    function clearPreview(message = "No image selected.") {
        preview.removeAttribute("src");
        preview.classList.add("hidden");
        placeholder.classList.remove("hidden");
        status.textContent = message;
    }

    input.addEventListener("change", () => {
        const file = input.files?.[0];
        if (!file) return clearPreview();
        if (!allowedTypes.has(file.type)) {
            input.value = "";
            clearPreview("Choose a PNG, JPEG, or WebP image.");
            return;
        }
        if (file.size > maxSize) {
            input.value = "";
            clearPreview("The selected image exceeds the 2 MB limit.");
            return;
        }

        const reader = new FileReader();
        reader.addEventListener("load", () => {
            preview.src = reader.result;
            preview.classList.remove("hidden");
            placeholder.classList.add("hidden");
            status.textContent = `${file.name} ready for preview.`;
        });
        reader.addEventListener("error", () => clearPreview("The image could not be read."));
        reader.readAsDataURL(file);
    });

    document.addEventListener("childguard:profile-cleared", () => clearPreview());
})();
