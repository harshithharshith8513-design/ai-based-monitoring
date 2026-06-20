(() => {
    const STORAGE_KEY = "childguard.profiles.v2";
    const LEGACY_KEY = "childguard.profile.v1";
    const form = document.getElementById("profile-form");
    const status = document.getElementById("storage-status");
    const list = document.getElementById("enrolled-profiles");
    const emptyState = document.getElementById("empty-profiles");
    const count = document.getElementById("profile-count");
    const cancelButton = document.getElementById("cancel-edit");
    const deleteAllButton = document.getElementById("delete-all-profiles");
    const fields = {
        id: document.getElementById("profile-id"),
        parentName: document.getElementById("parent-name"),
        childName: document.getElementById("child-name"),
        childAge: document.getElementById("child-age"),
        relationship: document.getElementById("relationship"),
        screenLimit: document.getElementById("screen-limit"),
        emergencyContact: document.getElementById("emergency-contact"),
        faceVerified: document.getElementById("face-verified"),
    };
    if (!form || !status || !list) return;

    const createId = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`;

    function readProfiles() {
        try {
            const profiles = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
            return Array.isArray(profiles) ? profiles : [];
        } catch {
            return [];
        }
    }

    function saveProfiles(profiles) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles));
    }

    function resetForm() {
        form.reset();
        fields.id.value = "";
        cancelButton?.classList.add("hidden");
        form.querySelector('[type="submit"]').textContent = "Enroll child";
        document.dispatchEvent(new CustomEvent("childguard:profile-cleared"));
    }

    function addDetail(container, label, value) {
        const row = document.createElement("p");
        row.className = "text-sm text-slate-600";
        const strong = document.createElement("strong");
        strong.className = "text-slate-900";
        strong.textContent = `${label}: `;
        row.append(strong, document.createTextNode(value || "Not provided"));
        container.append(row);
    }

    function renderProfiles() {
        const profiles = readProfiles();
        list.replaceChildren();
        count.textContent = `${profiles.length} ${profiles.length === 1 ? "child" : "children"}`;
        emptyState?.classList.toggle("hidden", profiles.length > 0);

        profiles.forEach((profile) => {
            const card = document.createElement("article");
            card.className = "profile-card";
            const heading = document.createElement("div");
            heading.className = "flex items-start justify-between gap-3";
            const title = document.createElement("h3");
            title.className = "text-xl font-extrabold text-slate-950";
            title.textContent = profile.childName;
            const badge = document.createElement("span");
            badge.className = profile.faceVerified ? "verified-badge" : "pending-badge";
            badge.textContent = profile.faceVerified ? "Face verified" : "Verification pending";
            heading.append(title, badge);

            const details = document.createElement("div");
            details.className = "mt-5 space-y-2";
            addDetail(details, "Age", profile.childAge);
            addDetail(details, "Caregiver", `${profile.parentName} (${profile.relationship})`);
            addDetail(details, "Screen limit", profile.screenLimit);
            addDetail(details, "Emergency", profile.emergencyContact);

            const actions = document.createElement("div");
            actions.className = "mt-6 flex gap-3";
            const edit = document.createElement("button");
            edit.type = "button";
            edit.className = "btn-secondary";
            edit.textContent = "Edit";
            edit.dataset.action = "edit";
            edit.dataset.id = profile.id;
            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "btn-danger";
            remove.textContent = "Remove";
            remove.dataset.action = "remove";
            remove.dataset.id = profile.id;
            actions.append(edit, remove);
            card.append(heading, details, actions);
            list.append(card);
        });
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!form.reportValidity()) return;
        const profiles = readProfiles();
        const profile = {
            id: fields.id.value || createId(),
            parentName: fields.parentName.value.trim(),
            childName: fields.childName.value.trim(),
            childAge: fields.childAge.value,
            relationship: fields.relationship.value,
            screenLimit: fields.screenLimit.value,
            emergencyContact: fields.emergencyContact.value.trim(),
            faceVerified: fields.faceVerified.checked,
            updatedAt: new Date().toISOString(),
        };
        const existingIndex = profiles.findIndex((item) => item.id === profile.id);
        if (existingIndex >= 0) profiles[existingIndex] = profile;
        else profiles.push(profile);
        try {
            saveProfiles(profiles);
            status.textContent = existingIndex >= 0
                ? `${profile.childName}'s profile was updated.`
                : `${profile.childName} was enrolled successfully.`;
            resetForm();
            renderProfiles();
        } catch {
            status.textContent = "Profile could not be saved. Browser storage may be unavailable.";
        }
    });

    list.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const profiles = readProfiles();
        const profile = profiles.find((item) => item.id === button.dataset.id);
        if (!profile) return;
        if (button.dataset.action === "remove") {
            saveProfiles(profiles.filter((item) => item.id !== profile.id));
            status.textContent = `${profile.childName} was removed from enrolled children.`;
            renderProfiles();
            return;
        }
        Object.entries(fields).forEach(([key, field]) => {
            if (key === "faceVerified") field.checked = Boolean(profile[key]);
            else field.value = profile[key] || "";
        });
        form.querySelector('[type="submit"]').textContent = "Update profile";
        cancelButton?.classList.remove("hidden");
        form.scrollIntoView({ behavior: "smooth", block: "start" });
        status.textContent = `Editing ${profile.childName}'s profile.`;
    });

    cancelButton?.addEventListener("click", () => {
        resetForm();
        status.textContent = "Editing cancelled.";
    });

    deleteAllButton?.addEventListener("click", () => {
        if (!readProfiles().length) {
            status.textContent = "There are no enrolled profiles to delete.";
            return;
        }
        if (!window.confirm("Delete every enrolled child profile from this browser?")) return;
        localStorage.removeItem(STORAGE_KEY);
        resetForm();
        renderProfiles();
        status.textContent = "All enrolled profiles were deleted.";
    });

    if (!localStorage.getItem(STORAGE_KEY)) {
        try {
            const legacy = JSON.parse(localStorage.getItem(LEGACY_KEY) || "null");
            if (legacy?.childName) {
                saveProfiles([{
                    id: createId(),
                    ...legacy,
                    childAge: "",
                    relationship: "Parent",
                    screenLimit: "2 hours",
                    faceVerified: false,
                }]);
                localStorage.removeItem(LEGACY_KEY);
            }
        } catch {
            localStorage.removeItem(LEGACY_KEY);
        }
    }
    renderProfiles();
})();
