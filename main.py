import os
import datetime
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

def main():
    pdf_folder = 'pdfs'
    dropbox_folder = '/GrantAlignTool'
    projects_folder = 'Projects'  # Local folder to store project files

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

    # Open the log file
    with open(log_file_path, "w") as log_file:
        # Debugging: Print folder paths
        log_file.write(f"Dropbox folder: {dropbox_folder}\n")
        log_file.write(f"Local PDF folder: {pdf_folder}\n")
        log_file.write(f"Projects folder: {projects_folder}\n")

        # Download PDFs from Dropbox (GrantAlignTool)
        grant_pages_path = 'grant_pages.txt'  # Path to the grant pages list in the same directory as main.py
        download_pdfs_from_dropbox(dropbox_folder, pdf_folder, refresh_token, client_id, client_secret, log_file, grant_pages_path)

        # Extract text from PDFs
        pdf_counter = 1
        for filename in os.listdir(pdf_folder):
            if filename.endswith('.pdf'):
                file_path = os.path.join(pdf_folder, filename)
                data += extract_text_from_pdf(file_path) + " "  # Add a space between texts
                # Print the current file number being processed
                print(f"Processing PDF {pdf_counter}")
                pdf_counter += 1

        log_file.write("Data from Dropbox:\n")
        log_file.write(data + "\n")

        # Download project files from Dropbox
        file_list_path = 'file_list.txt'  # Path to the file list in the same directory as main.py
        download_pdfs_from_dropbox(os.path.join(dropbox_folder, 'Projects'), projects_folder, refresh_token, client_id, client_secret, log_file, file_list_path)

        # Process each project file
        project_counter = 1
        for project_filename in os.listdir(projects_folder):
            if project_filename.endswith('.pdf'):
                project_file_path = os.path.join(projects_folder, project_filename)
                project_text = extract_text_from_pdf(project_file_path)

                # Build the questions
                questions = build_questions(project_text, data)
                all_answers = []
                combined_answers = ""

                # Initialize lists for each question type
                grouped_answers = [[] for _ in range(8)]

                for i, question in enumerate(questions, 1):
                    log_file.write(f"Built question {i} for {project_filename}: {question}\n")

                    # Run GPT-4 model
                    answer = run_gpt4all(question, log_file)
                    log_file.write(f"Answer for question {i} for {project_filename}: {answer}\n")
                    all_answers.append(answer)
                    combined_answers += " " + answer

                    # Group answers by question type
                    question_type_index = (i - 1) % 8  # 8 is the number of question options from question_builder.py
                    grouped_answers[question_type_index].append(answer)

                    # Print the current question number being processed
                    print(f"Processing question {i} for project {project_counter}")

                    # Summarize if there are more than 10 sentences
                    if (i % 10 == 0):
                        combined_answers = summarize_text(combined_answers)

                # Final summarization
                summary = summarize_text(combined_answers)

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
                    for j, answers in enumerate(grouped_answers, 1):
                        results_file.write(f"Question Type {j}:\n")
                        grouped_summary = summarize_text(' '.join(answers))
                        results_file.write(f"{grouped_summary}\n\n")

                # Upload the results file to Dropbox
                upload_file_to_dropbox(results_file_path, dropbox_folder, refresh_token, client_id, client_secret)

                # Print the completion of processing for the current project file
                print(f"Completed processing for project {project_counter}")
                project_counter += 1

    # Upload the log file to Dropbox
    upload_file_to_dropbox(log_file_path, dropbox_folder, refresh_token, client_id, client_secret)

if __name__ == "__main__":
    main()