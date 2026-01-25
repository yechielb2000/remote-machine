"""Cron actions."""

from __future__ import annotations

import shlex
from typing import List, Optional

from remote_machine.models.remote_state import RemoteState
from remote_machine.protocols.ssh import SSHProtocol
from remote_machine.models.common_types import OperationResult
from remote_machine.models.cron_types import (
    CronJob,
    CronSchedule,
    UserCronJobs,
    SystemCronFile,
)


class CronAction:
    """Cron job management."""

    def __init__(self, protocol: SSHProtocol, state: RemoteState):
        """Initialize cron actions.

        Args:
            protocol: SSH protocol instance
            state: Remote execution state
        """
        self.protocol = protocol
        self.state = state

    def _parse_cron_line(self, line: str) -> Optional[CronJob]:
        """Parse a cron line into CronJob object.

        Args:
            line: Cron line from crontab

        Returns:
            CronJob object or None if line is invalid
        """
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            return None

        # Parse cron format: minute hour day month weekday command
        # Can include optional: @yearly, @monthly, etc.
        parts = line.split(None, 5)

        if len(parts) < 6:
            return None

        try:
            return CronJob(
                minute=parts[0],
                hour=parts[1],
                day_of_month=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                command=parts[5] if len(parts) > 5 else "",
                comment=None,
            )
        except (ValueError, IndexError):
            return None

    def list_user_crons(self, username: Optional[str] = None) -> UserCronJobs:
        """List cron jobs for a user.

        Args:
            username: Username to list crons for. If None, lists current user's crons.

        Returns:
            UserCronJobs object with all jobs
        """
        if username:
            cmd = f"sudo crontab -u {shlex.quote(username)} -l"
        else:
            cmd = "crontab -l"

        output = self.protocol.run_command(cmd, self.state)

        jobs = []
        for line in output.strip().split("\n"):
            job = self._parse_cron_line(line)
            if job:
                jobs.append(job)

        return UserCronJobs(
            username=username or "current_user",
            jobs=jobs,
            last_modified=None,
        )

    def list_system_crons(self) -> List[SystemCronFile]:
        """List system-wide cron files.

        Returns:
            List of SystemCronFile objects
        """
        cron_dirs = ["/etc/cron.d", "/etc/cron.daily", "/etc/cron.weekly", "/etc/cron.monthly"]
        cron_files = ["/etc/crontab"]

        all_files = []

        # Read /etc/cron.d and subdirs
        for cron_dir in cron_dirs:
            try:
                output = self.protocol.run_command(f"ls -1 {cron_dir} 2>/dev/null", self.state)
                for filename in output.strip().split("\n"):
                    if filename:
                        file_path = f"{cron_dir}/{filename}"
                        all_files.append(file_path)
            except:
                continue

        # Add static cron files
        for cron_file in cron_files:
            try:
                self.protocol.run_command(f"test -f {cron_file}", self.state)
                all_files.append(cron_file)
            except:
                continue

        system_files = []
        for file_path in all_files:
            try:
                output = self.protocol.run_command(f"cat {shlex.quote(file_path)}", self.state)
                jobs = []
                for line in output.strip().split("\n"):
                    job = self._parse_cron_line(line)
                    if job:
                        jobs.append(job)

                system_files.append(SystemCronFile(path=file_path, jobs=jobs))
            except:
                continue

        return system_files

    def add_job(
        self,
        schedule: str,
        command: str,
        username: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> OperationResult:
        """Add a cron job.

        Args:
            schedule: Cron schedule (e.g., "0 2 * * *" for 2 AM daily)
            command: Command to execute
            username: Username to add job for. If None, adds to current user.
            comment: Optional comment for the job

        Returns:
            OperationResult indicating success or failure
        """
        # Get current crontab
        if username:
            try:
                current = self.protocol.run_command(
                    f"sudo crontab -u {shlex.quote(username)} -l", self.state
                )
            except:
                current = ""
        else:
            try:
                current = self.protocol.run_command("crontab -l", self.state)
            except:
                current = ""

        # Add new job
        lines = current.split("\n") if current else []

        if comment:
            lines.append(f"# {comment}")

        lines.append(f"{schedule} {command}")

        # Write back
        crontab_content = "\n".join(lines) + "\n"
        temp_file = "/tmp/crontab_temp"

        self.protocol.run_command(f"cat > {temp_file} << 'EOF'\n{crontab_content}EOF", self.state)

        if username:
            self.protocol.run_command(
                f"sudo crontab -u {shlex.quote(username)} {temp_file}", self.state
            )
        else:
            self.protocol.run_command(f"crontab {temp_file}", self.state)

        self.protocol.run_command(f"rm {temp_file}", self.state)

        return OperationResult(success=True, message=f"Cron job added: {command}")

    def remove_job(
        self,
        command: str,
        username: Optional[str] = None,
    ) -> OperationResult:
        """Remove a cron job by command.

        Args:
            command: Command to remove
            username: Username to remove job from. If None, removes from current user.

        Returns:
            OperationResult indicating success or failure
        """
        # Get current crontab
        if username:
            current = self.protocol.run_command(
                f"sudo crontab -u {shlex.quote(username)} -l", self.state
            )
        else:
            current = self.protocol.run_command("crontab -l", self.state)

        # Remove matching job
        lines = [line for line in current.split("\n") if line.strip() and command not in line]

        # Write back
        crontab_content = "\n".join(lines) + "\n"
        temp_file = "/tmp/crontab_temp"

        self.protocol.run_command(f"cat > {temp_file} << 'EOF'\n{crontab_content}EOF", self.state)

        if username:
            self.protocol.run_command(
                f"sudo crontab -u {shlex.quote(username)} {temp_file}", self.state
            )
        else:
            self.protocol.run_command(f"crontab {temp_file}", self.state)

        self.protocol.run_command(f"rm {temp_file}", self.state)

        return OperationResult(success=True, message=f"Cron job removed: {command}")

    def remove_all_jobs(self, username: Optional[str] = None) -> OperationResult:
        """Remove all cron jobs for a user.

        Args:
            username: Username to remove all jobs from. If None, removes current user's jobs.

        Returns:
            OperationResult indicating success or failure
        """
        if username:
            self.protocol.run_command(f"sudo crontab -u {shlex.quote(username)} -r", self.state)
        else:
            self.protocol.run_command("crontab -r", self.state)

        return OperationResult(success=True, message="All cron jobs removed")

    def validate_schedule(self, schedule: str) -> bool:
        """Validate a cron schedule string.

        Args:
            schedule: Cron schedule (e.g., "0 2 * * *")

        Returns:
            True if valid, False otherwise
        """
        # Simple validation: check for 5 fields
        parts = schedule.split()
        if len(parts) != 5:
            return False

        # Check each field
        ranges = [
            (0, 59),  # minute
            (0, 23),  # hour
            (1, 31),  # day of month
            (1, 12),  # month
            (0, 7),  # day of week
        ]

        for part, (min_val, max_val) in zip(parts, ranges):
            if part == "*":
                continue
            if part.startswith("*/"):
                try:
                    int(part[2:])
                    continue
                except ValueError:
                    return False
            if "-" in part:
                try:
                    start, end = part.split("-")
                    int(start)
                    int(end)
                    continue
                except ValueError:
                    return False
            try:
                val = int(part)
                if not (min_val <= val <= max_val):
                    return False
            except ValueError:
                return False

        return True

    def parse_schedule(self, schedule: str) -> Optional[CronSchedule]:
        """Parse a cron schedule into human-readable format.

        Args:
            schedule: Cron schedule (e.g., "0 2 * * *")

        Returns:
            CronSchedule object or None if invalid
        """
        if not self.validate_schedule(schedule):
            return None

        parts = schedule.split()
        minute, hour, day_of_month, month, day_of_week = parts

        # Build description
        desc_parts = []

        if hour != "*" and minute != "*":
            desc_parts.append(f"at {hour}:{minute}")
        elif hour != "*":
            desc_parts.append(f"at hour {hour}")
        elif minute != "*":
            desc_parts.append(f"at minute {minute}")

        if day_of_month != "*":
            desc_parts.append(f"on day {day_of_month}")

        if month != "*":
            desc_parts.append(f"in month {month}")

        if day_of_week != "*" and day_of_week != "0":
            days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            try:
                day_idx = int(day_of_week)
                if day_idx <= 7:
                    desc_parts.append(f"on {days[day_idx]}")
            except (ValueError, IndexError):
                pass

        description = " ".join(desc_parts) if desc_parts else "Run always"

        return CronSchedule(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month=month,
            day_of_week=day_of_week,
            description=description,
        )

    def get_job_logs(self, command_pattern: str = None) -> str:
        """Get cron job execution logs from syslog.

        Args:
            command_pattern: Optional pattern to filter logs

        Returns:
            Log output
        """
        if command_pattern:
            cmd = f"grep {shlex.quote(command_pattern)} /var/log/syslog 2>/dev/null | grep CRON || true"
        else:
            cmd = "grep CRON /var/log/syslog 2>/dev/null | tail -50 || true"

        return self.protocol.run_command(cmd, self.state)

    def is_cron_running(self) -> bool:
        """Check if cron daemon is running.

        Returns:
            True if cron is running, False otherwise
        """
        try:
            self.protocol.run_command(
                "systemctl is-active --quiet cron || systemctl is-active --quiet crond", self.state
            )
            return True
        except:
            return False

    def enable_cron(self) -> OperationResult:
        """Enable cron daemon.

        Returns:
            OperationResult indicating success or failure
        """
        # Try both cron and crond names (different distros)
        try:
            self.protocol.run_command("sudo systemctl enable cron", self.state)
        except:
            try:
                self.protocol.run_command("sudo systemctl enable crond", self.state)
            except:
                pass

        return OperationResult(success=True, message="Cron enabled")

    def start_cron(self) -> OperationResult:
        """Start cron daemon.

        Returns:
            OperationResult indicating success or failure
        """
        try:
            self.protocol.run_command("sudo systemctl start cron", self.state)
        except:
            try:
                self.protocol.run_command("sudo systemctl start crond", self.state)
            except:
                pass

        return OperationResult(success=True, message="Cron started")

    def stop_cron(self) -> OperationResult:
        """Stop cron daemon.

        Returns:
            OperationResult indicating success or failure
        """
        try:
            self.protocol.run_command("sudo systemctl stop cron", self.state)
        except:
            try:
                self.protocol.run_command("sudo systemctl stop crond", self.state)
            except:
                pass

        return OperationResult(success=True, message="Cron stopped")

    def restart_cron(self) -> OperationResult:
        """Restart cron daemon.

        Returns:
            OperationResult indicating success or failure
        """
        try:
            self.protocol.run_command("sudo systemctl restart cron", self.state)
        except:
            try:
                self.protocol.run_command("sudo systemctl restart crond", self.state)
            except:
                pass

        return OperationResult(success=True, message="Cron restarted")
