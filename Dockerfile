ARG STRATA_TOOLS_IMAGE=strata:local-rtx4070-tools
FROM ${STRATA_TOOLS_IMAGE}
COPY skills /opt/strata/custom-skills/skills
COPY runtime /opt/strata/custom-skills/runtime
ENV PYTHONDONTWRITEBYTECODE=1
