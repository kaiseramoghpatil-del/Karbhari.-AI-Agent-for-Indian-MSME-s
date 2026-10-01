# KARBHARI -- single image, two execution modes.
#
# Default (CMD): runs the normal web application (FastAPI serving its own
# API plus the built frontend) -- used for local hosting / API Endpoint
# submission.
#
# aiKart "Try Me Now" sandbox (Method 1 submission): the agent-manifest.yaml
# overrides the container's command to run the aiKart entrypoint script
# instead. Both paths call the exact same backend/app/services code --
# see backend/app/aikart/entrypoint.py -- this is one application, not two.

# ---- Stage 1: build the frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend runtime (final image) ----
FROM python:3.12-slim AS runtime
WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

ENV KARBHARI_DATA_DIR=/app/backend/data
RUN mkdir -p /app/backend/data/uploads

EXPOSE 8000

# Default: the web application. aiKart overrides this via its manifest's
# runtime.command to ["python", "-m", "app.aikart.entrypoint"] instead.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
