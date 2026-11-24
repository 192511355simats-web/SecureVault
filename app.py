
import os
import secrets

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename
from storage import UPLOAD_FOLDER

from database import get_connection, initialize_database
from backup import create_backup
from integrity import verify_backup
from restore import restore_backup
from key_rotation import rotate_encryption_keys
from scheduler import (
    add_schedule,
    get_all_schedules,
    delete_schedule,
    start_scheduler
)


# --------------------------------------------------
# FLASK APPLICATION CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
if (os.environ.get("RENDER") or os.environ.get("WEBSITE_SITE_NAME")) and not os.environ.get("FLASK_SECRET_KEY"):
    raise RuntimeError("FLASK_SECRET_KEY must be configured in production.")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# --------------------------------------------------
# DATABASE HELPER
# --------------------------------------------------

def get_backup_records():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM backups
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    connection.close()

    return records


# --------------------------------------------------
# 1. DASHBOARD
# --------------------------------------------------

@app.route("/")
def index():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM backups")
    total_backups = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM backups
        WHERE status = 'Verified'
    """)
    verified_backups = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM backups
        WHERE status = 'Integrity Failed'
    """)
    failed_backups = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM schedules
        WHERE status = 'Active'
    """)
    total_schedules = cursor.fetchone()[0]

    cursor.execute("""
        SELECT *
        FROM backups
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_backups = cursor.fetchall()

    connection.close()

    return render_template(
        "index.html",
        total_backups=total_backups,
        verified_backups=verified_backups,
        failed_backups=failed_backups,
        total_schedules=total_schedules,
        recent_backups=recent_backups
    )


# --------------------------------------------------
# 2. CREATE ENCRYPTED BACKUP
# --------------------------------------------------

@app.route("/backup", methods=["GET", "POST"])
def backup_page():

    if request.method == "POST":

        uploaded_file = request.files.get("file")

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please select a file.", "error")
            return redirect(url_for("backup_page"))

        file_name = secure_filename(uploaded_file.filename)

        if not file_name:
            flash("Invalid file name.", "error")
            return redirect(url_for("backup_page"))

        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        try:
            uploaded_file.save(file_path)

            backup_id = create_backup(file_path)

            flash(
                f"Encrypted backup created successfully! Backup ID: {backup_id}",
                "success"
            )

        except Exception as error:
            flash(f"Backup creation failed: {error}", "error")

        return redirect(url_for("backup_page"))

    backups = get_backup_records()

    return render_template(
        "backup.html",
        backups=backups
    )


# --------------------------------------------------
# 3. INTEGRITY VERIFICATION
# --------------------------------------------------

@app.route("/integrity", methods=["GET", "POST"])
def integrity_page():

    if request.method == "POST":

        backup_id = request.form.get("backup_id")

        try:
            if not backup_id:
                flash("Please select a backup.", "error")
            else:
                result = verify_backup(int(backup_id))

                if "failed" in result.lower() or "error" in result.lower():
                    flash(result, "error")
                else:
                    flash(result, "success")

        except Exception as error:
            flash(f"Integrity verification failed: {error}", "error")

        return redirect(url_for("integrity_page"))

    backups = get_backup_records()

    return render_template(
        "integrity.html",
        backups=backups
    )


# --------------------------------------------------
# 4. RESTORE BACKUP
# --------------------------------------------------

@app.route("/restore", methods=["GET", "POST"])
def restore_page():

    if request.method == "POST":

        backup_id = request.form.get("backup_id")

        try:
            if not backup_id:
                flash("Please select a backup to restore.", "error")
            else:
                result = restore_backup(int(backup_id))

                if "failed" in result.lower() or "error" in result.lower():
                    flash(result, "error")
                else:
                    flash(result, "success")

        except Exception as error:
            flash(f"Restore operation failed: {error}", "error")

        return redirect(url_for("restore_page"))

    backups = get_backup_records()

    return render_template(
        "restore.html",
        backups=backups
    )


# --------------------------------------------------
# 5. RECOVERY AUDIT
# --------------------------------------------------

@app.route("/audit")
def audit_page():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM audit_logs
        ORDER BY id DESC
    """)

    audit_records = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*)
        FROM audit_logs
        WHERE status = 'Success'
    """)

    successful_restores = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM audit_logs
        WHERE status = 'Failed'
    """)

    failed_restores = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "audit.html",
        audit_records=audit_records,
        successful_restores=successful_restores,
        failed_restores=failed_restores
    )


# --------------------------------------------------
# 6. ENCRYPTION KEY ROTATION
# --------------------------------------------------

@app.route("/rotate-keys", methods=["POST"])
def rotate_keys():

    try:
        result = rotate_encryption_keys()

        if "failed" in result.lower() or "error" in result.lower():
            flash(result, "error")
        else:
            flash(result, "success")

    except Exception as error:
        flash(f"Key rotation failed: {error}", "error")

    return redirect(url_for("index"))


# --------------------------------------------------
# 7. BACKUP SCHEDULING
# --------------------------------------------------

@app.route("/schedules", methods=["GET", "POST"])
def schedules_page():

    if request.method == "POST":

        file_path = request.form.get("file_path", "").strip()

        schedule_type = request.form.get("schedule_type", "").strip()

        try:
            if not file_path or not schedule_type:
                flash("Please enter a file path and schedule type.", "error")
            else:
                result = add_schedule(file_path, schedule_type)

                if isinstance(result, str):
                    if "failed" in result.lower() or "error" in result.lower():
                        flash(result, "error")
                    else:
                        flash(result, "success")
                else:
                    flash("Backup schedule added successfully.", "success")

        except Exception as error:
            flash(f"Unable to create schedule: {error}", "error")

        return redirect(url_for("schedules_page"))

    schedules = get_all_schedules()

    return render_template(
        "schedules.html",
        schedules=schedules
    )


# --------------------------------------------------
# 8. DELETE BACKUP SCHEDULE
# --------------------------------------------------

@app.route("/delete-schedule/<int:schedule_id>", methods=["POST"])
def delete_schedule_route(schedule_id):

    try:
        delete_schedule(schedule_id)
        flash("Backup schedule deleted successfully.", "success")

    except Exception as error:
        flash(f"Unable to delete schedule: {error}", "error")

    return redirect(url_for("schedules_page"))


# --------------------------------------------------
# APPLICATION START
# --------------------------------------------------

initialize_database()
start_scheduler()

if __name__ == "__main__":

    print("-----------------------------------------")
    print(" SECUREVAULT BACKUP SYSTEM")
    print("-----------------------------------------")
    print("Database initialized successfully.")
    print("Backup scheduler started successfully.")
    print("Open http://127.0.0.1:5000 in your browser.")
    print("-----------------------------------------")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        use_reloader=False,
    )
