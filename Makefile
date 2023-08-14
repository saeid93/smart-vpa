.PHONY: all install_gcloud download

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
hack_dir := $(PROJECT_DIR)/hack
install_gcloud := $(hack_dir)/smart-vpa/install-gcloud.sh
download := $(hack_dir)/download.sh

all: install_gcloud download
	@echo "Installation of all packages and dependencies completed"

install_gcloud:
	chmod +x $(install_gcloud)
	bash $(install_gcloud) PUBLIC_IP=$(PUBLIC_IP)
	@echo "install_gcloud.sh completed"

download:
	chmod +x $(download)
	bash $(download)
	@echo "download.sh completed"
