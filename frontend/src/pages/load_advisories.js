import {workspace} from '../workspace.js';

const page = {
  "title": "Theil–Sen 载重建议与复核",
  "module": "稳健载重建议",
  "caption": "稳健载重建议",
  "detail": "按车、路线和班次管理版本；复核员选定同一批新复核记录留出，比较新旧 MAE，只有误差更低才签认换版。",
  "path": "/load_advisories",
  "columns": [
    {"name": "code", "label": "编号"},
    {"name": "truck", "label": "参照车架"},
    {"name": "route", "label": "场内路线"},
    {"name": "cycle", "label": "适用班次"},
    {"name": "status", "label": "版本状态"},
    {"name": "rms_goal", "label": "合作社试车指标"},
    {"name": "ceiling_kg", "label": "建议装载上限 kg"},
    {"name": "slope", "label": "Theil–Sen 载重斜率"},
    {"name": "intercept", "label": "拟合截距凭据"},
    {"name": "validation_mae", "label": "本候选留出 MAE"},
    {"name": "baseline_mae", "label": "同批现行建议 MAE"},
    {"name": "exclusion_count", "label": "异动残差数"},
    {"name": "evidence_span", "label": "训练重量区间 kg"},
    {"name": "holdout_codes", "label": "指定留出记录"},
    {"name": "based_on", "label": "原建议"},
    {"name": "token", "label": "计算凭证"}
  ],
  "layout": "flip",
  "view": "table",
  "actions": [
    {
      "name": "fit_load",
      "label": "选择留出记录并试算",
      "path": "/load_advisories/fit-load",
      "fields": [
        {"name": "truck", "label": "参照车架", "kind": "text", "initial": "TRUCK-23"},
        {"name": "route", "label": "场内路线", "kind": "text", "initial": "EAST-REEF"},
        {"name": "cycle", "label": "适用班次", "kind": "text", "initial": "PM-02"},
        {"name": "rms_goal", "label": "试车指标", "kind": "float", "initial": 0.92},
        {
          "name": "holdout_codes",
          "label": "留出记录编号或 SENS 号（逗号分隔；留空用旧分层）",
          "kind": "text",
          "required": false,
          "initial": "OBS-E16,OBS-E17,OBS-E18,OBS-E19"
        },
        {
          "name": "based_on",
          "label": "原建议号（留空取车/路线/班次现行版）",
          "kind": "text",
          "required": false,
          "initial": ""
        }
      ],
      "help": "选定记录必须已复核且属于同路线同架型；它们不进训练，新旧模型按这同一批计算 MAE。试算期间仍照现行建议派车。",
      "roles": ["operator", "reviewer"],
      "success": "已写入"
    },
    {
      "name": "confirm_load",
      "label": "签认载重建议",
      "path": "/load_advisories/confirm-load",
      "fields": [
        {"name": "code", "label": "签认建议号", "kind": "text", "initial": "AD-QA"},
        {"name": "token", "label": "计算凭证", "kind": "token", "initial": ""},
        {
          "name": "based_on",
          "label": "同一原建议号（通常可留空）",
          "kind": "text",
          "required": false,
          "initial": ""
        }
      ],
      "help": "旧建议缺少拟合凭据、或同批 MAE 未更低时暂停换版。重复提交同一签认不会产生新版本；并发落后候选会按现行建议重算。",
      "roles": ["reviewer"],
      "success": "已签认并一次性切换现行建议"
    },
    {
      "name": "rebase_load",
      "label": "按现行建议重算候选",
      "path": "/load_advisories/rebase-load",
      "fields": [
        {"name": "token", "label": "落后候选的计算凭证", "kind": "token", "initial": ""},
        {
          "name": "based_on",
          "label": "现行建议号",
          "kind": "text",
          "required": false,
          "initial": ""
        }
      ],
      "help": "并发签认中另一份候选未生效时，用原留出批次和现行建议重新试算。",
      "roles": ["operator", "reviewer"],
      "success": "已提交重算"
    }
  ]
};

export const {title} = page;
export const key = "load_advisories";
export async function render(root, role) {
  await workspace(root, role, page);
}
