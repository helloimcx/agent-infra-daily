(() => {
  "use strict";
  const root = document.getElementById("intel-dashboard");
  if (!root) return;
  const prefix = root.dataset.root;
  const stats = document.getElementById("intel-stats");
  const trends = document.getElementById("intel-trends");
  const events = document.getElementById("intel-events");
  const audit = document.getElementById("intel-audit");
  const note = document.getElementById("intel-quality-note");
  const triage = document.getElementById("intel-triage");
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
  getJson("triage/latest.json").then(q => {
    const items = (q.items || []).slice(0, 8);
    if (!items.length) {
      empty(triage, "今日尚无待审阅候选，或每日快照尚未生成。");
      return;
    }
    triage.replaceChildren(...items.map(item => {
      const card = element("article", undefined, "intel-item");
      card.append(element("span", item.topic + " · 未核验候选", "intel-state"));
      const link = element("a", item.title);
      link.href = item.url;
      link.rel = "noopener noreferrer";
      link.target = "_blank";
      const heading = element("h3"); heading.append(link);
      card.append(heading, element("p", "来源：" + item.source_id +
        "。审阅排序依据：" + (item.review_order_reasons || []).join("、")),
        element("div", "请打开一手原文核对时间、架构意义和局限性", "subline"));
      return card;
    }));
  }).catch(() => empty(triage, "每日审阅队列尚未发布；待北京时间 06:30 快照入库。"));
  Promise.all([getJson("trends.json"), getJson("events.json"), getJson("quality/latest.json"), getJson("quality/coverage.json")])
    .then(([tr, ev, q, coverage]) => {
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
      if (coverage.gold_sample_size_eligible == null) {
        empty(audit, "已建立编辑核验基准集，首次定时评估尚待运行。");
      } else {
        const summary = element("article", undefined, "intel-item");
        summary.append(element("span", "小样本审计 · 不是行业召回率", "intel-state"),
          element("h3", "捕获 " + coverage.captured_count + " / " + coverage.gold_sample_size_eligible),
          element("p", "未监控来源：" + coverage.not_monitored_count +
            "；监控范围内漏报：" + coverage.in_scope_missed_count +
            "。来源覆盖缺失与采集错误分开计算。"));
        const cards = [summary];
        for (const entry of (coverage.reviewed_gold_items || [])) {
          const card = element("article", undefined, "intel-item");
          const labels = {captured:"已采集",source_not_monitored:"信源未覆盖",in_scope_not_observed:"范围内未发现"};
          card.append(element("span", labels[entry.outcome] || entry.outcome, "intel-state"),
            element("h3", entry.title),
            element("p", "真实事件日（北京）： " + entry.event_date_beijing));
          const source = element("a", "查看已核验原文 ↗");
          source.href = entry.primary_url;
          source.target = "_blank"; source.rel = "noopener noreferrer";
          card.append(source);
          cards.push(card);
        }
        audit.replaceChildren(...cards);
      }
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
      empty(audit, "审计数据尚不可用。");
      empty(trends, "尚无法读取趋势数据。");
      empty(events, "尚无法读取已核验事件。");
      note.textContent = "仪表板数据读取失败：" + error.message + "。检查文件是否已部署。";
      note.classList.add("intel-error");
    });
})();
