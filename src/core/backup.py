import platform
import subprocess
from os import makedirs, system

from src.core.config import Config


def database_backup_without_ssh():
    backup_dir = "./mysql/backups"
    if platform.system().lower() == "Linux".lower():
        makedirs(backup_dir, exist_ok=True)
        backup_command = f"mysqldump --databases {Config.CONNECTION_URL.database} \
            --single-transaction --no-tablespaces -Q -c -e \
            -u{Config.CONNECTION_URL.username} \
            -p{Config.CONNECTION_URL.password} \
            -h {Config.CONNECTION_URL.host} -P {Config.CONNECTION_URL.port} | gzip \
            > {backup_dir}/`date +backup.%Y%m%d_%H%M%S.sql.gz`"
        res = subprocess.run(backup_command, shell=True, capture_output=True, text=True)
        return {
            "command_status": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr,
        }

    elif platform.system().lower() == "Windows".lower():
        makedirs(backup_dir, exist_ok=True)
        res = system(f"mysqldump --databases {Config.CONNECTION_URL.database} \
            --single-transaction --no-tablespaces -Q -c -e \
            -u{Config.CONNECTION_URL.username} \
            -p{Config.CONNECTION_URL.password} \
            > backups/%date%_%time:~0,2%-%time:~3,2%-%time:~6,2%.sql")
        return res
