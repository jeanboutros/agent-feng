#!/usr/bin/env bash

# Create _libs directory
[ -d "_libs" ] || mkdir -p _libs

# Check if _libs/ is in .gitignore, if not add it
if ! grep -q "^_libs/$" .gitignore; then
    echo "_libs/" >> .gitignore
    echo "Added _libs/ to .gitignore"
else
    echo "_libs/ already in .gitignore"
fi

# Clone or update the repository
if [ -d "_libs/agent-panpan" ]; then
    echo "Repository exists, pulling latest changes..."
    cd _libs/agent-panpan
    git pull
    cd ../..
else
    echo "Cloning repository..."
    cd _libs
    git clone https://github.com/jeanboutros/agent-panpan.git
    cd ..
fi

# Create .github/agents directory if it doesn't exist
mkdir -p .github/agents

# Copy files from the repository to .github/agents
for file in _libs/agent-panpan/.github/agents/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        cp "$file" ".github/agents/$filename"
        echo "Copied: $filename"
    fi
done

echo "Setup complete! Agent files have been copied from the repository."
