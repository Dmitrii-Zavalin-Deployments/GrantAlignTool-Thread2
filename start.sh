#!/bin/bash

# Function to print a separator for better readability
print_separator() {
    echo "----------------------------------------"
}

# Function to check and install required packages
install_required_packages() {
    packages=("curl" "jq")
    for package in "${packages[@]}"; do
        if ! command -v $package &> /dev/null; then
            echo "Installing $package..."
            sudo apt-get update
            sudo apt-get install -y -f $package
        else
            echo "$package is already installed."
        fi
    done
}

# Function to refresh the access token
refresh_access_token() {
    local refresh_token=$1
    local client_id=$2
    local client_secret=$3
    local url="https://api.dropbox.com/oauth2/token"
    local data="grant_type=refresh_token&refresh_token=$refresh_token&client_id=$client_id&client_secret=$client_secret"
    local response=$(curl -s -X POST $url -d $data)
    echo $(echo $response | jq -r '.access_token')
}

# Function to download PDFs from Dropbox
download_pdfs_from_dropbox() {
    local dropbox_folder=$1
    local local_folder=$2
    local access_token=$3

    mkdir -p "$local_folder"
    local result=$(curl -s -X POST https://api.dropboxapi.com/2/files/list_folder \
        --header "Authorization: Bearer $access_token" \
        --header "Content-Type: application/json" \
        --data "{\"path\": \"$dropbox_folder\"}")

    local entries=$(echo $result | jq -c '.entries[]')
    for entry in $entries; do
        local name=$(echo $entry | jq -r '.name')
        local path_lower=$(echo $entry | jq -r '.path_lower')
        if [[ $name == *.pdf ]]; then
            curl -s -X POST https://content.dropboxapi.com/2/files/download \
                --header "Authorization: Bearer $access_token" \
                --header "Dropbox-API-Arg: {\"path\": \"$path_lower\"}" \
                --output "$local_folder/$name"
        fi
    done
}

# Check and install required packages
install_required_packages
print_separator

# Ask the user to enter Dropbox credentials
echo "Please enter your Dropbox credentials:"
read -p "Enter Dropbox App Key (client_id): " client_id
read -p "Enter Dropbox App Secret (client_secret): " client_secret
read -p "Enter Dropbox Refresh Token (refresh_token): " refresh_token
print_separator

# Ask the user to enter the project name from the Projects folder
read -p "Enter the name (without extension) of the project from the Projects folder: " project_name
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
pdf_dir="pdfs"
dropbox_folder="/GrantAlignTool"

# Ensure the pdfs folder is clean
echo "Cleaning up the folder $pdf_dir..."
rm -rf "$pdf_dir"
print_separator

# Refresh the access token
echo "Refreshing Dropbox access token..."
access_token=$(refresh_access_token $refresh_token $client_id $client_secret)
print_separator

# Download PDFs from Dropbox
echo "Downloading PDF files from Dropbox folder $dropbox_folder..."
download_pdfs_from_dropbox $dropbox_folder $pdf_dir $access_token
print_separator

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
    echo "${run_files_no_ext[@]}" > "$grant_pages_file"
    echo "$project_name" > "$file_list_file"
    print_separator

    # Push the changes to the repository
    echo "Pushing changes to the repository $repo_url..."
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

# Delete the pdfs folder
echo "Deleting the folder $pdf_dir..."
rm -rf "$pdf_dir"
print_separator

echo "All tasks completed successfully!"