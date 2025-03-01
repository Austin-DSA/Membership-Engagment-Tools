# Define variables for each project
PROJECTS := list_management recommit_drive_2022

DEFAULT_PROJECT := list_management

# Help target to show available make commands
help:
	@echo "Usage:"
	@echo "  make build PROJECT=<project_name>      Build a project (e.g. make build PROJECT=ListManagement)"
	@echo "  make start PROJECT=<project_name>         Start a project with Docker Compose"
	@echo "  make stop PROJECT=<project_name>       Stop the Docker Compose environment"

# Build target
build:
	@if [ -z "$(PROJECT)" ]; then \
		PROJECT=$(DEFAULT_PROJECT); \
	fi
	@docker-compose -f docker/docker-compose.yml build $(PROJECT)

# Up target (start the container)
start:
	@if [ -z "$(PROJECT)" ]; then \
		PROJECT=$(DEFAULT_PROJECT); \
	fi
	@docker-compose -f docker/docker-compose.yml up $(PROJECT)

# Down target (stop the container)
stop:
	@if [ -z "$(PROJECT)" ]; then \
		PROJECT=$(DEFAULT_PROJECT); \
	fi
	@docker-compose -f docker/docker-compose.yml down $(PROJECT)
