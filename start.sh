#!/bin/bash

# Function to print a separator for better readability
print_separator() {
    echo "----------------------------------------"
}

echo "Run this script from the local computer"
print_separator

# Ask the user to enter the path to the local GrantAlignTool folder
read -p "Enter the path to your local GrantAlignTool folder: " grantaligntool_path
print_separator

# Ask the user to enter project names from the Projects folder
read -p "Enter the names (without extension) of the projects from the Projects folder, separated by commas (e.g., 'project1' for one project or 'project1, project2' for two projects): " project_names
print_separator

# Split the project names into an array
IFS=',' read -r -a project_names_array <<< "$project_names"

# Log the project names array
echo "Project names array: ${project_names_array[@]}"
print_separator

# Ask the user to enter the number of runs or use default value 15
read -p "Enter the number of runs (default is 15): " num_runs
num_runs=${num_runs:-15}
if [ $num_runs -gt 15 ]; then
    echo "Error: The number of runs cannot exceed 15."
    exit 1
fi
print_separator

# Ask the user to enter the path to the SSH key file
read -p "Enter the path to your SSH key file: " ssh_key_path
print_separator

# Add the SSH key to the SSH agent
echo "Adding SSH key to the SSH agent..."
eval "$(ssh-agent -s)"
ssh-add "$ssh_key_path"
print_separator

# Directory containing the PDF files
pdf_dir="$grantaligntool_path"

# Get all PDF file names from the directory and store them in an array
echo "Fetching PDF files from $pdf_dir..."
pdf_files=($(ls "$pdf_dir"/*.pdf | xargs -n 1 basename))
echo "Found ${#pdf_files[@]} PDF files."
print_separator

# Calculate the number of files per run
num_files=${#pdf_files[@]}
files_per_run=$((num_files / num_runs))
remainder=$((num_files % num_runs))

# Split the array into the number of runs
echo "Splitting files into $num_runs runs..."
start_index=0
for ((i=0; i<num_runs; i++)); do
    end_index=$((start_index + files_per_run))
    if [ $i -lt $remainder ]; then
        end_index=$((end_index + 1))
    fi
    run_files=("${pdf_files[@]:start_index:end_index-start_index}")
    run_files_no_ext=("${run_files[@]%.pdf}")  # Remove the .pdf extension
    echo "Run $((i+1)) files: ${run_files_no_ext[@]}"
    start_index=$end_index
    print_separator

    # Clone the appropriate repository
    repo_url="git@github.com:Dmitrii-Zavalin-Deployments/GrantAlignTool-Thread$((i+1)).git"
    repo_dir="GrantAlignTool-Thread$((i+1))"
    echo "Cloning repository $repo_url..."
    git clone "$repo_url" "$repo_dir"
    print_separator

    # Add files to grant_pages.txt and file_list.txt
    echo "Updating grant_pages.txt and file_list.txt in $repo_dir..."
    grant_pages_file="$repo_dir/grant_pages.txt"
    file_list_file="$repo_dir/file_list.txt"
    echo "Deleting the content of the file_list.txt..."
    > "$file_list_file"
    printf "%s\n" "${run_files_no_ext[@]}" > "$grant_pages_file"
    for project_name in "${project_names_array[@]}"; do
        project_name=$(echo "$project_name" | xargs)  # Trim any leading/trailing whitespace
        echo "Processing project name: $project_name"
        if ! grep -qx "$project_name" "$file_list_file"; then
            echo "Adding project name to file_list.txt: $project_name"
            echo "$project_name" >> "$file_list_file"
        else
            echo "Project name already exists in file_list.txt: $project_name"
        fi
    done
    print_separator

    # Push the changes to the repository
    echo "Pushing changes to the repository $repo_url..."
    echo "$repo_dir"
    cd "$repo_dir"
    git add grant_pages.txt file_list.txt
    git commit -m "Update grant_pages.txt and file_list.txt for run $((i+1))"
    git push origin master
    cd ..
    print_separator

    # Delete the local repository folder
    echo "Deleting the local repository folder $repo_dir..."
    rm -rf "$repo_dir"
    print_separator
done

echo "All tasks completed successfully!"