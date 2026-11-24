
document.addEventListener("DOMContentLoaded", function () {

    // Display selected file name
    const fileInput = document.querySelector('input[type="file"]');

    if (fileInput) {
        fileInput.addEventListener("change", function () {
            if (this.files.length > 0) {
                console.log("Selected file: " + this.files[0].name);
            }
        });
    }

    // Confirm backup creation
    const backupForm = document.querySelector(
        'form[action*="backup"]'
    );

    if (backupForm) {
        backupForm.addEventListener("submit", function (event) {
            if (!confirm("Do you want to create an encrypted backup?")) {
                event.preventDefault();
            }
        });
    }

    // Confirm key rotation
    const rotateForm = document.querySelector(
        'form[action*="rotate"]'
    );

    if (rotateForm) {
        rotateForm.addEventListener("submit", function (event) {
            if (!confirm("Are you sure you want to rotate encryption keys?")) {
                event.preventDefault();
            }
        });
    }

    console.log("Backup Recovery System JavaScript loaded.");
});
