
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import get_connection, initialize_database
from backup import create_backup

scheduler = BackgroundScheduler()


def run_scheduled_backup(file_path):
    """Execute an automatic backup."""

    if not os.path.isfile(file_path):
        print(f"Scheduled file not found: {file_path}")
        return

    try:
        create_backup(file_path)
        print(f"Scheduled backup completed: {file_path}")

        # Update the next scheduled run
        update_next_run(file_path)

    except Exception as error:
        print(f"Scheduled backup failed: {error}")


def update_next_run(file_path):
    """Update the next execution time in SQLite."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, schedule_type FROM schedules "
        "WHERE file_name = ? AND status = 'Active'",
        (file_path,)
    )

    records = cursor.fetchall()

    for record in records:
        hours = {
            "hourly": 1,
            "daily": 24,
            "weekly": 168
        }.get(record["schedule_type"].lower())

        if hours:
            next_run = datetime.now() + timedelta(hours=hours)

            cursor.execute(
                "UPDATE schedules SET next_run = ? WHERE id = ?",
                (
                    next_run.strftime("%Y-%m-%d %H:%M:%S"),
                    record["id"]
                )
            )

    connection.commit()
    connection.close()


def add_schedule(file_path, schedule_type):
    """Create a new backup schedule."""

    initialize_database()

    file_path = os.path.abspath(file_path)

    if not os.path.isfile(file_path):
        return "Selected file does not exist."

    intervals = {
        "hourly": 1,
        "daily": 24,
        "weekly": 168
    }

    schedule_type = schedule_type.lower()

    if schedule_type not in intervals:
        return "Invalid schedule type."

    hours = intervals[schedule_type]

    next_run = datetime.now() + timedelta(hours=hours)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO schedules
        (file_name, schedule_type, next_run, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            file_path,
            schedule_type,
            next_run.strftime("%Y-%m-%d %H:%M:%S"),
            "Active"
        )
    )

    schedule_id = cursor.lastrowid

    connection.commit()
    connection.close()

    if scheduler.running:
        scheduler.add_job(
            run_scheduled_backup,
            trigger=IntervalTrigger(hours=hours),
            args=[file_path],
            id=str(schedule_id),
            replace_existing=True
        )

    return "Backup schedule created successfully."


def load_schedules():
    """Load saved active schedules from the database."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM schedules WHERE status = 'Active'"
    )

    records = cursor.fetchall()
    connection.close()

    intervals = {
        "hourly": 1,
        "daily": 24,
        "weekly": 168
    }

    for record in records:
        hours = intervals.get(record["schedule_type"].lower())

        if hours:
            scheduler.add_job(
                run_scheduled_backup,
                trigger=IntervalTrigger(hours=hours),
                args=[record["file_name"]],
                id=str(record["id"]),
                replace_existing=True
            )


def start_scheduler():
    """Start the background scheduler."""

    if not scheduler.running:
        load_schedules()
        scheduler.start()
        print("Backup scheduler started successfully.")


def get_all_schedules():
    """Get all saved backup schedules."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM schedules ORDER BY id DESC"
    )

    records = cursor.fetchall()
    connection.close()

    return records


def delete_schedule(schedule_id):
    """Delete a saved schedule."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM schedules WHERE id = ?",
        (schedule_id,)
    )

    connection.commit()
    connection.close()

    if scheduler.running:
        job = scheduler.get_job(str(schedule_id))

        if job:
            scheduler.remove_job(str(schedule_id))

    return "Backup schedule deleted successfully."


def run_due_schedules():
    """Run due schedules. This can be called by an external free-tier timer."""

    initialize_database()
    now = datetime.now()
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, file_name, schedule_type FROM schedules "
        "WHERE status = 'Active' AND next_run <= ? ORDER BY id",
        (now.strftime("%Y-%m-%d %H:%M:%S"),)
    )
    due_schedules = cursor.fetchall()
    connection.close()

    completed = 0
    failed = 0
    intervals = {"hourly": 1, "daily": 24, "weekly": 168}

    for schedule in due_schedules:
        file_path = schedule["file_name"]
        hours = intervals.get(schedule["schedule_type"].lower())
        try:
            if not hours:
                raise ValueError("Invalid schedule type.")
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Scheduled file not found: {file_path}")
            create_backup(file_path)
            completed += 1
        except Exception as error:
            failed += 1
            print(f"Scheduled backup failed for {file_path}: {error}")
        finally:
            if hours:
                next_run = now + timedelta(hours=hours)
                connection = get_connection()
                connection.execute(
                    "UPDATE schedules SET next_run = ? WHERE id = ?",
                    (next_run.strftime("%Y-%m-%d %H:%M:%S"), schedule["id"])
                )
                connection.commit()
                connection.close()

    return {"due": len(due_schedules), "completed": completed, "failed": failed}
