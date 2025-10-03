import subprocess
import sys
import os  # <--- ADD THIS LINE
from colorama import init, Fore, Style

init(autoreset=True)

def run_agent(agent_name: str):
    """Runs a Python script as a separate process and prints the output."""
    print(Fore.YELLOW + f"[*] Running {agent_name}...")
    try:
        # --- START OF CHANGES ---
        # Set an environment variable to force Python to use UTF-8 for I/O
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        
        process = subprocess.Popen(
            [sys.executable, f"agents\\{agent_name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=my_env  # <-- ADD THIS ARGUMENT
        )
        # --- END OF CHANGES ---

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        if process.returncode == 0:
            print(Fore.GREEN + f"[+] {agent_name} finished successfully.\n")
        else:
            print(Fore.RED + f"[-] {agent_name} failed with return code {process.returncode}.\n")

    except FileNotFoundError:
        print(Fore.RED + f"[!] Error: {agent_name} not found. Make sure the script exists in the 'agents' directory.")
    except Exception as e:
        print(Fore.RED + f"[!] An unexpected error occurred while running {agent_name}: {e}")

if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "===================================")
    print(Style.BRIGHT + Fore.CYAN + "  Running Invoice Processing Pipeline")
    print(Style.BRIGHT + Fore.CYAN + "===================================\n")

    agents_to_run = [
        "ingestion_agent.py",
        "validation_agent.py",
        "logger_agent.py",
        "mapper_agent.py",
        "gst_fetcher_agent.py",
        "reviewer_agent.py"
    ]

    for agent in agents_to_run:
        run_agent(agent)

    print(Style.BRIGHT + Fore.CYAN + "===================================")
    print(Style.BRIGHT + Fore.CYAN + "  Pipeline finished.")
    print(Style.BRIGHT + Fore.CYAN + "===================================")