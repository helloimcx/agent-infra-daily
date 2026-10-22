(() => {
  "use strict";
  const root = document.getElementById("intel-dashboard");
  if (!root) return;
  const prefix = root.dataset.root;
  const stats = document.getElementById("intel-stats");
  const trends = document.getElementById("intel-trends");
  const events = document.getElementById("intel-events");
  const note = document.getElementById("intel-quality-note");
  const element = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = String(text);
    if (className) el.className = className;
    return el;
  };
  function empty(target, text) { target.replaceChildren(element("p", text)); }
  async function getJson(file) {
    const response = await fetch(prefix + file, {cache: "no-store"});
    if (!response.ok) throw new Error(file + " HTTP " + response.status);
    return response.json();
  }
  Promise.all([getJson("trends.json"), getJson("events.json"), getJson("quality/latest.json")])
    .then(([tr, ev, q]) => {
      const health = q.source_health || {};
      const cm = q.candidate_metrics || {};
      const cards = [
        ["信源检查", health.total != null ? health.healthy + " / " + health.total : "—", health.failed ? health.failed + " 个失败" : "正常或无采集数据"],
        ["事件候选", cm.cross_day_candidates_retained ?? "—", "滚动 90 天上限"],
        ["已核验事件", (ev.events || []).filter(x => x.status === "verified").length, "不由 RSS 自动生成"],
        ["趋势命题", (tr.trends || []).length, "证据驱动修订"]
      ];
      stats.replaceChildren(...cards.map(([label,value,sub]) => {
        const box = element("div", undefined, "intel-stat");
        box.append(element("span", label), element("strong", value), element("small", sub));
        return box;
      }));
      const when = q.generated_at || "尚未运行首次汇总";
      note.textContent = "数据更新时间：" + when +
        "。健康率衡量采集可用性，不衡量重大事件发现率；事件候选属于未核验信息，源数不代表独立印证。" +
        (health.failed ? " 存在失败信源，请检查工作流日志。" : "");
      if (!(tr.trends || []).length) empty(trends, "暂时没有长期假设。");
      else trends.replaceChildren(...tr.trends.map(t => {
        const card = element("article", undefined, "intel-item");
        const tag = element("span", (t.status || "unassessed") + " · " + (t.confidence || "unassessed"), "intel-state");
        card.append(tag, element("h3", t.title), element("p", t.hypothesis));
        const boundary = element("div", undefined, "intel-falsifier");
        boundary.append(element("b", "反证条件"), element("p", t.falsification));
        card.append(boundary, element("div", (t.evidence_event_ids || []).length + " 个已核验事件关联", "subline"));
        return card;
      }));
      const verified = (ev.events || []).filter(e => e.status === "verified").slice().reverse();
      if (!verified.length) empty(events, "目前尚无已核验的正式事件。候选文章不会自动冒充事实。");
      else events.replaceChildren(...verified.slice(0, 30).map(e => {
        const card = element("article", undefined, "intel-item");
        card.append(element("span", e.event_date + " · " + e.topic, "intel-state"), element("h3", e.title));
        const details = element("div", undefined, "subline");
        details.textContent = "核验来源 " + e.evidence.length + " 条 · " + (e.verification?.reviewed_by || "未知");
        card.append(details);
        for (const src of (e.evidence || []).slice(0, 3)) {
          const a = element("a", src.title || src.url);
          a.href = src.url; a.rel = "noopener noreferrer"; a.target = "_blank";
          const p = element("p"); p.append(a); card.append(p);
        }
        return card;
      }));
    })
    .catch(error => {
      empty(trends, "尚无法读取趋势数据。");
      empty(events, "尚无法读取已核验事件。");
      note.textContent = "仪表板数据读取失败：" + error.message + "。检查文件是否已部署。";
      note.classList.add("intel-error");
    });
})();
