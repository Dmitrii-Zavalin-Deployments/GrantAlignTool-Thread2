#!/bin/bash

# Function to print a separator for better readability
print_separator() {
    echo "----------------------------------------"
}

# Print the initial message
echo "Run the script from the auxiliary_scripts folder within the core directory of GrantAlignTool."
print_separator

# Get the absolute path of the GrantAlignTool directory
grant_align_tool_path=$(realpath ../../GrantAlignTool)

# Copy the update_repos.sh script to the GrantAlignTool directory
echo "Copying update_repos.sh to the GrantAlignTool directory..."
cp update_repos.sh "$grant_align_tool_path/update_repos_temp.sh"
print_separator

# Run the copied script from the GrantAlignTool directory
echo "Running the update_repos_temp.sh script from the GrantAlignTool directory..."
(cd "$grant_align_tool_path" && bash update_repos_temp.sh "$grant_align_tool_path")
print_separator

# Clean up by removing the temporary script
echo "Cleaning up the temporary script..."
rm "$grant_align_tool_path/update_repos_temp.sh"
print_separator

echo "All repositories have been updated."