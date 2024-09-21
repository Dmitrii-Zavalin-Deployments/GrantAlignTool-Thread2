#!/bin/bash

# Function to print a separator for better readability
print_separator() {
    echo "----------------------------------------"
}

# Print the initial message
echo "Run the script from the auxiliary_scripts folder within the core directory of GrantAlignTool."
print_separator

# Get the absolute path of the GrantAlignTool directory
cd ../..
grant_align_tool_path=$(pwd)

# Copy the update_repos.sh script to the GrantAlignTool directory
echo "Copying update_repos.sh to the GrantAlignTool directory..."
cp GrantAlignTool/auxiliary_scripts/update_repos.sh .
print_separator

# Run the copied script from the GrantAlignTool directory
echo "Running the update_repos.sh script from the outside of GrantAlignTool directory..."
./update_repos.sh
print_separator

# Clean up by removing the temporary script
echo "Cleaning up the temporary script..."
rm update_repos.sh
print_separator

echo "All repositories have been updated."