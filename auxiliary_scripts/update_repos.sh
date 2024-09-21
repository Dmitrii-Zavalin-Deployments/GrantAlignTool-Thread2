#!/bin/bash

# Function to print a separator for better readability
print_separator() {
    echo "----------------------------------------"
}

# Ask the user to enter the path to the SSH key file
read -p "Enter the path to your SSH key file: " ssh_key_path
print_separator

# Add the SSH key to the SSH agent
echo "Adding SSH key to the SSH agent..."
eval "$(ssh-agent -s)"
ssh-add "$ssh_key_path"
print_separator

# Define the base repository name and the range of repositories
base_repo="GrantAlignTool-Thread"
start=1
end=15

# Get the local repository path from the argument
local_repo="GrantAlignTool"

# Define your GitHub username
github_username="Dmitrii-Zavalin-Deployments"

# Loop through the range of repositories
for i in $(seq $start $end); do
    # Define the repository name
    repo_name="${base_repo}${i}"

    echo "Processing repository: ${repo_name}"
    print_separator

    # Clone the repository
    echo "Cloning ${repo_name}..."
    git clone git@github.com:${github_username}/${repo_name}.git
    if [ $? -ne 0 ]; then
        echo "Failed to clone ${repo_name}. Skipping..."
        print_separator
        continue
    fi

    # Change to the repository directory
    cd ${repo_name}
    
    # Check if the repository is empty
    if [ -z "$(ls -A .)" ]; then
        echo "Repository ${repo_name} is empty. Creating initial commit..."
        touch README.md
        git add README.md
        git commit -m "Initial commit"
        git branch -M master
        git push -u origin master
    else
        # Ensure we are on the master branch
        git checkout master

        # Pull the latest changes from the remote repository
        echo "Pulling latest changes from the remote repository..."
        git pull origin master
    fi

    # Delete all files and folders except .git
    echo "Deleting all files and folders except .git..."
    rm -rf *
    rm -rf .github

    # Copy the contents from the local repository to the cloned repository, excluding the .git directory and the repo_name directory
    echo "Copying files from ${local_repo} to ${repo_name}..."
    cp -r ../${local_repo}/* .
    cp -r ../${local_repo}/.github .

    # Add, commit, and push the changes
    echo "$(pwd)"
    echo "Adding files to ${repo_name}..."
    git add .
    echo "Committing changes in ${repo_name}..."
    git commit -m "Copied files from ${local_repo}"
    echo "Pushing changes to ${repo_name}..."
    git push origin master
    if [ $? -ne 0 ]; then
        echo "Failed to push changes to ${repo_name}. Skipping..."
        cd ..
        rm -rf ${repo_name}
        print_separator
        continue
    fi

    # Change back to the parent directory
    cd ..

    # Remove the cloned repository to clean up
    echo "Cleaning up ${repo_name}..."
    rm -rf ${repo_name}

    echo "Finished processing ${repo_name}."
    print_separator
done

echo "All repositories have been updated."