# use aws lambda python 3.13 base image (matches pyproject requires-python)
FROM public.ecr.aws/lambda/python:3.13

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# copy dependency files first for caching
COPY pyproject.toml uv.lock ${LAMBDA_TASK_ROOT}/

# install dependencies into .venv (no project source yet)
RUN uv sync --frozen --no-install-project

# add .venv/lib/python3.13/site-packages to PYTHONPATH so lambda finds them
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/.venv/lib/python3.13/site-packages:${LAMBDA_TASK_ROOT}"

# copy source code
COPY . ${LAMBDA_TASK_ROOT}/

# set default command (can be overridden in serverless.yml)
CMD [ "handlers.lambda_handler.api_handler" ]
# bump
