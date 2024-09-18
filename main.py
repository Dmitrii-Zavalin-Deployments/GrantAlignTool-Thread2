import os
import datetime
import requests
import json
from extract_text_from_pdf import extract_text_from_pdf
from download_from_dropbox import download_pdfs_from_dropbox, upload_file_to_dropbox
from gpt4all_functions import run_gpt4all
from question_builder import build_questions

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

def summarize_text(text, max_sentences=10):
    sentences = text.split('. ')
    if len(sentences) <= max_sentences:
        return text
    if len(sentences) > 50:
        max_sentences = 15
    elif len(sentences) > 100:
        max_sentences = 20
    summary = '. '.join(sentences[:max_sentences])
    return summary

def save_state(state, state_file):
    with open(state_file, 'w') as f:
        json.dump(state, f)

def load_state(state_file):
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return None

def main():
    pdf_folder = 'pdfs'
    dropbox_folder = '/GrantAlignTool'
    projects_folder = 'Projects'  # Local folder to store project files
    state_file = 'state.json'

    # Fetch secrets from environment variables
    client_id = os.getenv('DROPBOX_APP_KEY')
    client_secret = os.getenv('DROPBOX_APP_SECRET')
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

    # Refresh the access token
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    data = ""

    # Create a unique log file name
    log_file_name = f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_file_path = os.path.join(pdf_folder, log_file_name)

    # Ensure the local folders exist
    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(projects_folder, exist_ok=True)

    # Load previous state if exists
    state = load_state(state_file)
    if state is None:
        state = {
            "step": "start",
            "pdf_counter": 1,
            "project_counter": 1,
            "question_counter": 1,
            "combined_answers": "",
            "grouped_answers": [[] for _ in range(8)]
        }

    # Open the log file
    with open(log_file_path, "w") as log_file:
        def log_and_print(message):
            log_file.write(message + "\n")
            log_file.flush()  # Ensure the message is written to the file immediately
            print(message)

        # Debugging: Print folder paths
        log_and_print(f"Dropbox folder: {dropbox_folder}")
        log_and_print(f"Local PDF folder: {pdf_folder}")
        log_and_print(f"Projects folder: {projects_folder}")

        if state["step"] == "start":
            log_and_print("Step: start")
            # Download PDFs from Dropbox
            download_pdfs_from_dropbox(dropbox_folder, pdf_folder, refresh_token, client_id, client_secret, log_file)
            state["step"] = "extract_text"
            save_state(state, state_file)

        if state["step"] == "extract_text":
            log_and_print("Step: extract_text")
            # Extract text from PDFs
            for filename in os.listdir(pdf_folder):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(pdf_folder, filename)
                    data += extract_text_from_pdf(file_path)
                    # Print the current file number being processed
                    log_and_print(f"Processing PDF {state['pdf_counter']}")
                    state["pdf_counter"] += 1
            log_and_print("Data from Dropbox:")
            log_and_print(data)
            state["step"] = "download_projects"
            save_state(state, state_file)

        if state["step"] == "download_projects":
            log_and_print("Step: download_projects")
            # Download project files from Dropbox
            file_list_path = 'file_list.txt'  # Path to the file list in the same directory as main.py
            download_pdfs_from_dropbox(os.path.join(dropbox_folder, 'Projects'), projects_folder, refresh_token, client_id, client_secret, log_file, file_list_path)
            state["step"] = "process_projects"
            save_state(state, state_file)

        if state["step"] == "process_projects":
            log_and_print("Step: process_projects")
            # Process each project file
            project_files = os.listdir(projects_folder)
            for project_filename in project_files[state["project_counter"]-1:]:
                if project_filename.endswith('.pdf'):
                    project_file_path = os.path.join(projects_folder, project_filename)
                    project_text = extract_text_from_pdf(project_file_path)

                    # Build the questions
                    questions = build_questions(project_text, data)
                    all_answers = state["combined_answers"]

                    for i, question in enumerate(questions[state["question_counter"]-1:], state["question_counter"]):
                        log_and_print(f"Built question {i} for {project_filename}: {question}")

                        # Run GPT-4 model
                        answer = run_gpt4all(question, log_file)
                        log_and_print(f"Answer for question {i} for {project_filename}: {answer}")
                        all_answers += " " + answer

                        # Group answers by question type
                        question_type_index = (i - 1) % 8  # 8 is the number of question options from question_builder.py
                        state["grouped_answers"][question_type_index].append(answer)

                        # Print the current question number being processed
                        log_and_print(f"Processing question {i} for project {state['project_counter']}")

                        # Summarize if there are more than 10 sentences
                        if (i % 10 == 0):
                            all_answers = summarize_text(all_answers)

                        state["question_counter"] = i + 1
                        save_state(state, state_file)

                    # Final summarization
                    summary = summarize_text(all_answers)

                    # Remove the extension from project_filename
                    project_name = os.path.splitext(project_filename)[0]

                    # Create results file with a unique name
                    results_file_name = f"result_{project_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    results_file_path = os.path.join(pdf_folder, results_file_name)
                    with open(results_file_path, "w") as results_file:
                        results_file.write(f"Log file: {log_file_name}\n\n")
                        results_file.write("Summary:\n")
                        results_file.write(summary + "\n\n")
                        results_file.write("Grouped Answers:\n")
                        for j, answers in enumerate(state["grouped_answers"], 1):
                            results_file.write(f"Question Type {j}:\n")
                            grouped_summary = summarize_text(' '.join(answers))
                            results_file.write(f"{grouped_summary}\n\n")

                    # Upload the results file to Dropbox
                    upload_file_to_dropbox(results_file_path, dropbox_folder, refresh_token, client_id, client_secret)

                    # Print the completion of processing for the current project file
                    log_and_print(f"Completed processing for project {state['project_counter']}")
                    state["project_counter"] += 1
                    state["question_counter"] = 1
                    state["combined_answers"] = ""
                    state["grouped_answers"] = [[] for _ in range(8)]
                    save_state(state, state_file)

        # Ensure the log file is properly closed before uploading
        log_file.close()

        # Upload the log file to Dropbox
        upload_file_to_dropbox(log_file_path, dropbox_folder, refresh_token, client_id, client_secret)

        # Clean up state file after successful run
        if os.path.exists(state_file):
            os.remove(state_file)

if __name__ == "__main__":
    main()