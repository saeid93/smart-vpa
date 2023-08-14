function install_gcloud() {
    echo "Installing Google Cloud SDK"
    # wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-430.0.0-linux-x86_64.tar.gz -O gcloud.tar.gz
    # tar -xf gcloud.tar.gz
    # bash ./google-cloud-sdk/install.sh -q
    # other distros need different installation
    sudo apt-get install -y apt-transport-https ca-certificates gnupg curl sudo
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    sudo apt-get update && sudo apt-get install google-cloud-cli
    echo "Google Cloud SDK installation complete"
    echo
}

install_gcloud