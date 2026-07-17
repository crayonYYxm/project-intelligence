export const buildSkillNamePattern = (skillNames) => {
  const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp([...skillNames].sort((left, right) => right.length - left.length).map(escapeRegExp).join("|"), "g");
};

export const skillToolInvocations = (stdout, skillNamePattern) => {
  const found = [];
  for (const line of stdout.split(/\r?\n/)) {
    if (!line.trim().startsWith("{")) continue;
    let value;
    try {
      value = JSON.parse(line);
    } catch {
      continue;
    }
    const visit = (item) => {
      if (!item || typeof item !== "object") return;
      const type = String(item.type ?? "").toLowerCase();
      const name = String(item.name ?? item.tool_name ?? item.toolName ?? "").toLowerCase();
      const explicitSkillEvent = new Set(["skill", "skill_use", "skill_call", "skill_invocation"]).has(type);
      const skillToolEvent = /(?:tool|function)(?:_use|_call)?/.test(type) && /skill/.test(name);
      if (explicitSkillEvent || skillToolEvent) {
        const body = JSON.stringify(item.input ?? item.arguments ?? item.skill ?? item);
        for (const match of body.matchAll(skillNamePattern)) found.push(match[0]);
      }
      for (const child of Array.isArray(item) ? item : Object.values(item)) visit(child);
    };
    visit(value);
  }
  return found;
};

export const evaluateSkillRoute = (scenario, actual) => {
  const expected = scenario.expectedSkills ?? [];
  const allowed = new Set([...expected, ...(scenario.allowedSkills ?? [])]);
  const missing = expected.filter((skill) => !actual.includes(skill));
  const forbidden = (scenario.forbiddenSkills ?? []).filter((skill) => actual.includes(skill));
  const unexpected = [...new Set(actual.filter((skill) => !allowed.has(skill)))];
  const positions = (scenario.expectedOrder ?? []).map((skill) => actual.indexOf(skill));
  const ordered = positions.every((value, index) => value >= 0 && (index === 0 || value > positions[index - 1]));
  return { missing, forbidden, unexpected, ordered };
};
