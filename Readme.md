# Grant Alignment Tool

## Overview
This tool aligns project descriptions with grant requirements using GPT-4All. It processes PDF files containing project descriptions and grant requirements, and generates alignment results.

## Usage
1. **Prepare PDF files**:
    - **Project Descriptions**: Place PDF files with project descriptions in the Dropbox folder `/GrantAlignTool/Projects`.
    - **Grant Requirements**: Place PDF files with grant requirements in the Dropbox folder `/GrantAlignTool`.

2. **Update Dropbox Access Token**:
    - Generate a new Dropbox access token for the needed application from Dropbox Developers: Dropbox Developers: https://www.dropbox.com/developers/apps.
    - Update the Dropbox access token in GitHub Actions Secrets.

3. **Prepare `file_list.txt` and `grant_pages.txt`**:
    - Ensure the `file_list.txt` file exists in the same directory as `main.py` and `download_from_dropbox.py`.
    - List the names of the project files (without extensions) you want to download from the `Projects` folder. If this file is empty or doesn't exist, all PDFs in the `Projects` folder will be downloaded.
    - Ensure the `grant_pages.txt` file exists in the same directory as `main.py` and `download_from_dropbox.py`.
    - List the names of the grant requirement files (without extensions) you want to download from the `GrantAlignTool` folder. If this file is empty or doesn't exist, all PDFs in the `GrantAlignTool` folder will be downloaded.

4. **Run the script**:
    - Trigger the job on GitHub Actions after all the PDF files are uploaded.

5. **Important**:
    - Process one grant at a time. After running the script, delete or move the grant PDF files to avoid confusion for the next run.

## Multi-Run Option
For multiple runs, clone this repository and use the `start.sh` script. Follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Dmitrii-Zavalin-Deployments/GrantAlignTool
    cd GrantAlignTool
    ```

2. **Run the `start.sh` script**:
    ```bash
    ./start.sh
    ```

3. **Script Details**:
    - The script will prompt you to enter your Dropbox credentials, project name, number of runs, and the path to your SSH key file.
    - It will refresh the Dropbox access token, download PDFs, and split them into the specified number of runs.
    - For each run, it will clone a specific repository, update `grant_pages.txt` and `file_list.txt`, and push the changes.

## Output
- **Results**: Generated results files are uploaded to the Dropbox folder `/GrantAlignTool`.
- **Logs**: Log files are uploaded to the Dropbox folder `/GrantAlignTool`.

## Notes
- Ensure the `Projects` folder in Dropbox contains only the project description PDFs.
- The script processes each project file and generates a unique result file for each.

## Example
1. **Project Descriptions**:
    - `/GrantAlignTool/Projects/project1.pdf`
    - `/GrantAlignTool/Projects/project2.pdf`

2. **Grant Requirements**:
    - `/GrantAlignTool/grant1.pdf`

3. **Run the script**:
    - Trigger the job on GitHub Actions.

4. **Output**:
    - Results and log files will be uploaded to Dropbox.