import os
import datetime
import requests
from gpt4all_functions import run_gpt4all

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
        return response.json()["access_token"]
    else:
        raise Exception("Failed to refresh access token")

def download_files_from_dropbox(folder_path, local_path, access_token):
    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "path": folder_path
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception("Failed to list files in Dropbox folder")

    files = response.json().get('entries', [])
    for file in files:
        if file['.tag'] == 'file':
            download_url = "https://content.dropboxapi.com/2/files/download"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Dropbox-API-Arg": f'{{"path": "{file["path_lower"]}"}}'
            }
            response = requests.post(download_url, headers=headers)
            if response.status_code == 200:
                local_file_path = os.path.join(local_path, file['name'])
                with open(local_file_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded {file['name']} to {local_file_path}")
            else:
                print(f"Failed to download {file['name']}")

def upload_file_to_dropbox(local_file_path, dropbox_folder, access_token):
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": f'{{"path": "{dropbox_folder}/{os.path.basename(local_file_path)}", "mode": "overwrite"}}',
        "Content-Type": "application/octet-stream"
    }
    with open(local_file_path, 'rb') as f:
        data = f.read()
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to upload {local_file_path} to Dropbox")

def split_text_by_characters(text, max_chars=6000):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

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

    # Download result files from Dropbox
    download_files_from_dropbox(dropbox_folder, summary_folder, access_token)

    # Combine texts from all result files
    text_to_summary = ""
    result_files = [f for f in os.listdir(summary_folder) if 'result' in f and f.endswith('.txt')]
    for result_file in result_files:
        with open(os.path.join(summary_folder, result_file), 'r') as file:
            text_to_summary += file.read() + " "

    # Create a log file
    log_file_name = f"log_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_file_path = os.path.join(summary_folder, log_file_name)
    with open(log_file_path, 'w') as log_file:
        # Split the text into chunks of no more than 6000 characters each
        chunks = split_text_by_characters(text_to_summary)

        # Summarize each chunk to get no more than 250 tokens
        chunk_summaries = []
        for chunk in chunks:
            chunk_summary = run_gpt4all(chunk, log_file)
            chunk_summaries.append(chunk_summary)

        # Combine all chunk summaries into one variable
        final_summary = " ".join(chunk_summaries)

    # Read the content of file_list.txt from the same directory as summary.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_list_path = os.path.join(script_dir, 'file_list.txt')
    if not os.path.exists(file_list_path):
        raise FileNotFoundError(f"{file_list_path} not found. Please ensure the file exists.")

    with open(file_list_path, 'r') as file_list:
        file_list_content = file_list.read().strip()

    # Create the final summary file with the number of result files in the name
    final_summary_file_name = f"{file_list_content}_project_grant_alignment_summary_{len(result_files)}.txt"
    final_summary_file_path = os.path.join(summary_folder, final_summary_file_name)
    with open(final_summary_file_path, 'w') as final_summary_file:
        final_summary_file.write(f"Summarized {len(result_files)} result files\n\n")
        final_summary_file.write("Summary:\n")
        final_summary_file.write(final_summary)

    # Upload the final summary file to Dropbox
    upload_file_to_dropbox(final_summary_file_path, dropbox_folder, access_token)

if __name__ == "__main__":
    main()