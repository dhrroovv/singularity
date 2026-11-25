# Define the base image to use for the container
FROM python:3.12-slim

# Pin a specific uv version here for reproducible builds
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Sets the working directory for every later instruction and for the running container 
# Relative paths such as ./ mean /app
WORKDIR /app

# Sets the environment variables for the container
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"

# Copies the pyproject.toml and uv.lock files to the container
COPY pyproject.toml uv.lock ./

# Installs the dependencies for the project
RUN uv sync --frozen --no-dev

# Copies the rest of the project files to the container
COPY . .

# Runs the FastAPI application
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
