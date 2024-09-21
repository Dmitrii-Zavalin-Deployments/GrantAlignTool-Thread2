import os
import datetime
import requests
import dropbox
import time

def refresh_access_token(refresh_token, client_id, client_secret):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        return access_token
    else:
        error_message = "Failed to refresh access token"
        raise Exception(error_message)

def list_all_files(dbx, folder_path, log_file):
    files = []
    try:
        result = dbx.files_list_folder(folder_path)
        files.extend(result.entries)
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            files.extend(result.entries)
    except dropbox.exceptions.ApiError as err:
        error_message = f"Error listing files: {err}"
        log_file.write(f"{error_message}\n")
    return files

def download_files_from_dropbox(folder_path, local_path, refresh_token, client_id, client_secret, log_file):
    # Refresh the access token
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)
    log_file.write("Dropbox client initialized.\n")
    try:
        os.makedirs(local_path, exist_ok=True)
        log_file.write(f"Local path '{local_path}' ensured.\n")

        files = list_all_files(dbx, folder_path, log_file)
        log_file.write(f"Listing files in Dropbox folder: {folder_path}\n")

        for entry in files:
            log_file.write(f"Found entry: {entry.name} ({entry.path_lower})\n")
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.endswith('.txt') and 'result' in entry.name:
                local_file_path = os.path.join(local_path, entry.name)
                with open(local_file_path, "wb") as f:
                    metadata, res = dbx.files_download(path=entry.path_lower)
                    f.write(res.content)
                log_file.write(f"Downloaded {entry.name} to {local_file_path}\n")
        log_file.write("Download completed.\n")
    except dropbox.exceptions.ApiError as err:
        error_message = f"Error downloading files: {err}"
        log_file.write(f"{error_message}\n")
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        log_file.write(f"{error_message}\n")

def upload_file_to_dropbox(local_file_path, dropbox_folder, access_token, log_file):
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": f'{{"path": "{dropbox_folder}/{os.path.basename(local_file_path)}", "mode": "overwrite"}}',
        "Content-Type": "application/octet-stream"
    }
    with open(local_file_path, 'rb') as f:
        data = f.read()
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        log_message = f"Uploaded {local_file_path} to Dropbox"
        log_file.write(log_message + "\n")
    else:
        log_message = f"Failed to upload {local_file_path} to Dropbox"
        log_file.write(log_message + "\n")
        raise Exception(log_message)

def parse_log_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    log_dict = {}
    start_parsing = False
    current_question = None

    for line in lines:
        line = line.strip()
        if line.startswith("Question Type 1:"):
            start_parsing = True
        if start_parsing:
            if line.startswith("Question Type"):
                current_question = line.split(": ", 1)[0]
                log_dict[current_question] = ""
            elif current_question and line:
                log_dict[current_question] = line
                current_question = None

    return log_dict

def write_summary_to_file(summary_dict, output_file, num_files):
    with open(output_file, 'w') as file:
        file.write(f"Grouped Answers from {num_files} result files\n\n")
        for question_type, answer in summary_dict.items():
            file.write(f"{question_type}\n{answer}\n\n")

def main():
    dropbox_folder = '/GrantAlignTool'
    summary_folder = 'summary'

    # Fetch secrets from environment variables
    client_id = os.getenv('DROPBOX_APP_KEY')
    client_secret = os.getenv('DROPBOX_APP_SECRET')
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

    # Refresh the access token
    access_token = refresh_access_token(refresh_token, client_id, client_secret)

    # Ensure the local folder exists
    os.makedirs(summary_folder, exist_ok=True)

    # Create a log file
    log_file_name = f"log_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_file_path = os.path.join(summary_folder, log_file_name)
    with open(log_file_path, 'w') as log_file:
        log_message = "Log file created."
        log_file.write(log_message + "\n")

        # Download result files from Dropbox
        download_files_from_dropbox(dropbox_folder, summary_folder, refresh_token, client_id, client_secret, log_file)

        # Debugging: List files in the summary folder
        files_in_summary = os.listdir(summary_folder)
        log_message = f"Files in {summary_folder}: {files_in_summary}"
        log_file.write(log_message + "\n")

        # Combine texts from all result files
        log_data_dicts = {}
        summary_dict = {}
        result_files = [f for f in files_in_summary if 'result' in f and f.endswith('.txt')]
        log_message = f"Found {len(result_files)} result files."
        log_file.write(log_message + "\n")
        for result_file in result_files:
            file_path = os.path.join(summary_folder, result_file)
            log_data_dicts[result_file] = parse_log_file(file_path)

        # Combine dictionaries into a summary dictionary
        for file_path, log_data in log_data_dicts.items():
            for question_type, answer in log_data.items():
                if question_type in summary_dict:
                    summary_dict[question_type] += " " + answer
                else:
                    summary_dict[question_type] = answer

        # Read the content of file_list.txt from the same directory as summary.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_list_path = os.path.join(script_dir, 'file_list.txt')
        if not os.path.exists(file_list_path):
            log_message = f"{file_list_path} not found. Please ensure the file exists."
            log_file.write(log_message + "\n")
            raise FileNotFoundError(log_message)

        with open(file_list_path, 'r') as file_list:
            file_list_content = file_list.read().strip()

        # Create the final summary file with the number of result files in the name
        final_summary_file_name = f"{file_list_content}_project_grant_alignment_summary_{len(result_files)}.txt"
        final_summary_file_path = os.path.join(summary_folder, final_summary_file_name)
        write_summary_to_file(summary_dict, final_summary_file_path, len(result_files))
        log_message = f"Summary written to {final_summary_file_path}"
        log_file.write(log_message + "\n")

        # Upload the final summary file to Dropbox
        upload_file_to_dropbox(final_summary_file_path, dropbox_folder, access_token, log_file)

        # Ensure the log file is flushed and closed before uploading
        log_file.flush()
        os.fsync(log_file.fileno())
        log_file.close()

        # Upload the log file to Dropbox
        upload_file_to_dropbox(log_file_path, dropbox_folder, access_token, open(log_file_path, 'a'))

if __name__ == "__main__":
    main()