ARG STRATA_TOOLS_IMAGE=strata:local-rtx4070-tools
FROM ${STRATA_TOOLS_IMAGE}
COPY skills /opt/strata/custom-skills/skills
COPY runtime /opt/strata/custom-skills/runtime
RUN /opt/strata/.venv/bin/python /opt/strata/custom-skills/runtime/patch_web.py /opt/strata/serve/web/app.js
ENV PYTHONDONTWRITEBYTECODE=1
