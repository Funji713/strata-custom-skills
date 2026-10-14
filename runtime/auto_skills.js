function strataApplyAutoSkills(body, info) {
  if (body.strata_mcp !== true || !(info.servers || []).some((server) =>
    server.name === "skills" && server.status === "ready" &&
    (server.tools || []).some((tool) => tool.name === "skills__read_skill"))) return;
  body.messages = [{role: "system", content: STRATA_AUTO_SKILLS_PROMPT}, ...body.messages];
}
