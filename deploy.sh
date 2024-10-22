#!/bin/bash

echo "deleting old app"
sudo rm -rf /var/www/

echo "creating app folder"
sudo mkdir -p /var/www/ncucampuseats-app

echo "moving files to app folder"
sudo mv * /var/www/ncucampuseats-app

# Navigate to the app directory
cd /var/www/ncucampuseats-app/

# Ensure Python venv package is installed
echo "installing python3-venv"
sudo apt-get update
sudo apt-get install -y python3-venv

# Create a virtual environment
echo "creating a virtual environment"
python3 -m venv env

# Activate the virtual environment
echo "activating virtual environment"
source env/bin/activate

# Upgrade pip
echo "upgrading pip"
pip install --upgrade pip

# Install application dependencies from requirements.txt
echo "Install application dependencies from requirements.txt"
pip install -r requirements.txt

# Update and install Nginx if not already installed
if ! command -v nginx > /dev/null; then
    echo "Installing Nginx"
    sudo apt-get update
    sudo apt-get install -y nginx
fi

# Configure Nginx to act as a reverse proxy if not already configured
if [ ! -f /etc/nginx/sites-available/myapp ]; then
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo bash -c 'cat > /etc/nginx/sites-available/myapp <<EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/ncucampuseats-app/myapp.sock;
    }
}
EOF'

    sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled
    sudo systemctl restart nginx
else
    echo "Nginx reverse proxy configuration already exists."
fi

# Stop any existing Gunicorn process
sudo pkill gunicorn
sudo rm -rf myapp.sock

# Start Gunicorn with the Flask application
echo "starting gunicorn"
sudo env PATH="/var/www/ncucampuseats-app/env/bin:$PATH" gunicorn --workers 3 --bind unix:myapp.sock app:app --user www-data --group www-data --daemon
echo "started gunicorn 🚀"
