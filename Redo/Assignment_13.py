import logging
import os

# Set up the output directory and file path
log_directory = "assignment13"
os.makedirs(log_directory, exist_ok=True)  # Create the directory if it doesn't exist
log_path = os.path.join(log_directory, "app.log")

# Step 1: Configure logging (initially to log everything)
logging.basicConfig(
    filename=log_path,
    filemode="w",  # Overwrites file each time
    level=logging.ERROR,  # Change to logging.ERROR in Step 2
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Step 2: Write log messages of various severity levels
logging.debug("This is a DEBUG message.")
logging.info("This is an INFO message.")
logging.warning("This is a WARNING message.")
logging.error("This is an ERROR message.")

print(f"Log file written to: {log_path}")