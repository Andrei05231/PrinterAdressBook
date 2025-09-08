# Konica Admin Tool Makefile
# Easy commands for setup, login, and testing

# Directories
SCRIPTS_DIR := scripts
VENV_DIR := venv

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help venv install login test clean

# Default target
help:
	@echo "$(BLUE)Konica Admin Tool - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  make venv          - Create a Python virtual environment"
	@echo "  make install       - Install dependencies"
	@echo ""
	@echo "$(YELLOW)Actions:$(NC)"
	@echo "  make login         - Login to all configured printers"
	@echo "  make logout        - Logout from all configured printers"
	@echo "  make address_book  - Get address book from all configured printers"
	@echo ""
	@echo "$(YELLOW)Utilities:$(NC)"
	@echo "  make clean         - Remove temporary files"

# Create virtual environment
venv:
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	python3 -m venv $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created at $(VENV_DIR)$(NC)"

# Install dependencies
install: venv
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/python -m pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

# Run login script
login:
	@echo "$(GREEN)Logging in to all printers...$(NC)"
	$(VENV_DIR)/bin/python -m scripts.login_all

# Run logout script
logout:
	@echo "${(GREEN)}Logging out all printer..."
	$(VENV_DIR)/bin/python -m scripts.logout_all

# Get Adress book from all printers
address_book:
	@echo "Getting Adress books"
	$(VENV_DIR)/bin/python -m scripts.get_adress_books

# Clean temporary files
clean:
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete$(NC)"

