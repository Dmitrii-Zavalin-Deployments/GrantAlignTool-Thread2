import os
import datetime
import json
import requests
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

def save_progress(progress_file, progress_data):
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)

def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return None

def main():
    pdf_folder = 'pdfs'
    dropbox_folder = '/GrantAlignTool'
    projects_folder = 'Projects'
    progress_file = 'progress.json'

    client_id = os.getenv('DROPBOX_APP_KEY')
    client_secret = os.getenv('DROPBOX_APP_SECRET')
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')

    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    data = ""

    # Ensure the local folders exist
    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(projects_folder, exist_ok=True)

    # Load progress data
    progress_data = load_progress(progress_file)
    if progress_data is None:
        progress_data = {
            "pdf_counter": 1,
            "project_counter": 1,
            "questions_processed": 0,
            "combined_answers": "",
            "grouped_answers": [[] for _ in range(8)],
            "completed": False
        }

    # Determine log file path
    if progress_data["completed"]:
        log_file_name = f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        results_file_name = f"result_{progress_data['project_counter']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        progress_data["completed"] = False
    else:
        log_file_name = 'current_log.txt'
        results_file_name = 'current_result.txt'
    log_file_path = os.path.join(pdf_folder, log_file_name)
    results_file_path = os.path.join(pdf_folder, results_file_name)

    # Open log file in append mode if it exists, otherwise create a new one
    with open(log_file_path, "a") as log_file:
        log_file.write(f"Dropbox folder: {dropbox_folder}\n")
        log_file.write(f"Local PDF folder: {pdf_folder}\n")
        log_file.write(f"Projects folder: {projects_folder}\n")

        if progress_data["pdf_counter"] == 1:
            download_pdfs_from_dropbox(dropbox_folder, pdf_folder, refresh_token, client_id, client_secret, log_file)

        for filename in os.listdir(pdf_folder):
            if filename.endswith('.pdf') and progress_data["pdf_counter"] > 1:
                file_path = os.path.join(pdf_folder, filename)
                data += extract_text_from_pdf(file_path)
                print(f"Processing PDF {progress_data['pdf_counter']}")
                progress_data["pdf_counter"] += 1
                save_progress(progress_file, progress_data)

        log_file.write("Data from Dropbox:\n")
        log_file.write(data + "\n")

        if progress_data["project_counter"] == 1:
            file_list_path = 'file_list.txt'
            download_pdfs_from_dropbox(os.path.join(dropbox_folder, 'Projects'), projects_folder, refresh_token, client_id, client_secret, log_file, file_list_path)

        # Process each project file
        project_counter = 1
        log_file.write("Starting to process project files...\n")
        for project_filename in os.listdir(projects_folder):
            if project_filename.endswith('.pdf'):
                project_file_path = os.path.join(projects_folder, project_filename)
                project_text = extract_text_from_pdf(project_file_path)

                questions = build_questions(project_text, data)
                for i, question in enumerate(questions, 1):
                    if i <= progress_data["questions_processed"]:
                        continue

                    log_file.write(f"Built question {i} for {project_filename}: {question}\n")
                    answer = run_gpt4all(question, log_file)
                    log_file.write(f"Answer for question {i} for {project_filename}: {answer}\n")
                    progress_data["combined_answers"] += " " + answer
                    question_type_index = (i - 1) % 8
                    progress_data["grouped_answers"][question_type_index].append(answer)
                    print(f"Processing question {i} for project {progress_data['project_counter']}")
                    progress_data["questions_processed"] = i
                    save_progress(progress_file, progress_data)

                    if i % 10 == 0:
                        progress_data["combined_answers"] = summarize_text(progress_data["combined_answers"])

                summary = summarize_text(progress_data["combined_answers"])
                project_name = os.path.splitext(project_filename)[0]

                # Open result file in append mode if it exists, otherwise create a new one
                with open(results_file_path, "a") as results_file:
                    results_file.write(f"Log file: {log_file_name}\n\n")
                    results_file.write("Summary:\n")
                    results_file.write(summary + "\n\n")
                    results_file.write("Grouped Answers:\n")
                    for j, answers in enumerate(progress_data["grouped_answers"], 1):
                        results_file.write(f"Question Type {j}:\n")
                        grouped_summary = summarize_text(' '.join(answers))
                        results_file.write(f"{grouped_summary}\n\n")

                upload_file_to_dropbox(results_file_path, dropbox_folder, refresh_token, client_id, client_secret)
                print(f"Completed processing for project {progress_data['project_counter']}")
                progress_data["project_counter"] += 1
                progress_data["questions_processed"] = 0
                progress_data["combined_answers"] = ""
                progress_data["grouped_answers"] = [[] for _ in range(8)]
                save_progress(progress_file, progress_data)

    upload_file_to_dropbox(log_file_path, dropbox_folder, refresh_token, client_id, client_secret)

    # Mark the run as completed
    progress_data["completed"] = True
    save_progress(progress_file, progress_data)

    # Rename log and result files upon completion
    new_log_file_name = f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    new_results_file_name = f"result_{progress_data['project_counter']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.rename(log_file_path, os.path.join(pdf_folder, new_log_file_name))
    if os.path.exists(results_file_path):
        os.rename(results_file_path, os.path.join(pdf_folder, new_results_file_name))

if __name__ == "__main__":
    main()