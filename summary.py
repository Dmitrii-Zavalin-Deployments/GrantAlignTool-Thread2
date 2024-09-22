import os
import sys
import datetime

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
    if len(sys.argv) != 2:
        print("Usage: python3 summary.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        sys.exit(1)

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Create a log file
    log_file_name = f"log_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_file_path = os.path.join(directory, log_file_name)
    with open(log_file_path, 'w') as log_file:
        log_message = "Log file created."
        log_file.write(log_message + "\n")

        # Debugging: List files in the directory
        files_in_directory = os.listdir(directory)
        log_message = f"Files in {directory}: {files_in_directory}"
        log_file.write(log_message + "\n")

        # Combine texts from all result files
        log_data_dicts = {}
        summary_dict = {}
        result_files = [f for f in files_in_directory if 'result' in f and f.endswith('.txt')]
        log_message = f"Found {len(result_files)} result files."
        log_file.write(log_message + "\n")
        for result_file in result_files:
            file_path = os.path.join(directory, result_file)
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
        final_summary_file_name = f"project_grant_alignment_summary_{len(result_files)}.txt"
        final_summary_file_path = os.path.join(directory, final_summary_file_name)
        write_summary_to_file(summary_dict, final_summary_file_path, len(result_files))
        log_message = f"Summary written to {final_summary_file_path}"
        log_file.write(log_message + "\n")

        # Ensure the log file is flushed and closed
        log_file.flush()
        os.fsync(log_file.fileno())
        log_file.close()

if __name__ == "__main__":
    main()