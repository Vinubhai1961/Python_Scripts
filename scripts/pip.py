import subprocess
import sys


def upgrade_selenium():
    try:
        # Command to upgrade pip first (ensures compatibility)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

        # Command to upgrade selenium
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "selenium"])
        print("Selenium has been successfully upgraded.")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while upgrading Selenium: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    upgrade_selenium()