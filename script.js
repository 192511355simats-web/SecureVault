
// =======================================
// SECUREVAULT - JAVASCRIPT
// =======================================

document.addEventListener("DOMContentLoaded", function () {

    // FILE UPLOAD DISPLAY
    const fileInput = document.getElementById("backupFile");
    const fileName = document.getElementById("fileName");

    if (fileInput && fileName) {

        fileInput.addEventListener("change", function () {

            if (fileInput.files.length > 0) {

                fileName.textContent =
                    "Selected File: " + fileInput.files[0].name;

            } else {

                fileName.textContent = "No file selected";

            }

        });

    }

    // RESTORE CONFIRMATION
    const restoreForm = document.querySelector(
        'form[action="/restore"]'
    );

    if (restoreForm) {

        restoreForm.addEventListener("submit", function (event) {

            const selectedBackup =
                restoreForm.querySelector('[name="backup_id"]');

            if (!selectedBackup || !selectedBackup.value) {
                event.preventDefault();
                alert("Please select a backup version.");
                return;
            }

            if (!confirm("Do you want to restore this backup?")) {
                event.preventDefault();
            }

        });

    }

    // INTEGRITY VERIFICATION VALIDATION
    const integrityForm = document.querySelector(
        'form[action="/integrity"]'
    );

    if (integrityForm) {

        integrityForm.addEventListener("submit", function (event) {

            const selectedBackup =
                integrityForm.querySelector('[name="backup_id"]');

            if (!selectedBackup || !selectedBackup.value) {
                event.preventDefault();
                alert("Please select a backup to verify.");
            }

        });

    }

    // BACKUP FORM VALIDATION
    const backupForm = document.querySelector(
        'form[action="/backup"]'
    );

    if (backupForm) {

        backupForm.addEventListener("submit", function (event) {

            const selectedFile =
                backupForm.querySelector('[name="file"]');

            if (!selectedFile || selectedFile.files.length === 0) {
                event.preventDefault();
                alert("Please select a file before creating a backup.");
            }

        });

    }

    // ACTIVE NAVIGATION HIGHLIGHT
    const currentPath = window.location.pathname;

    document.querySelectorAll(".nav-link").forEach(function (link) {

        if (link.getAttribute("href") === currentPath) {

            link.classList.add("active");

        } else {

            link.classList.remove("active");

        }

    });

    console.log("SecureVault JavaScript loaded successfully.");

});
