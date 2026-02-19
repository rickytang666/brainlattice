# use aws lambda python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# copy dependency files first for caching
COPY pyproject.toml uv.lock ${LAMBDA_TASK_ROOT}/

# install dependencies into .venv
RUN uv sync --frozen

# add .venv/lib/python3.12/site-packages to PYTHONPATH so lambda finds them
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/.venv/lib/python3.12/site-packages:${LAMBDA_TASK_ROOT}"

# copy source code
COPY . ${LAMBDA_TASK_ROOT}/

# set default command (can be overridden in serverless.yml)
CMD [ "handlers.lambda_handler.api_handler" ]
