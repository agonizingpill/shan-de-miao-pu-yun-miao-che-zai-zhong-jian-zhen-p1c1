        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "Theil–Sen 载重建议与复核",
  "module": "稳健载重建议",
  "caption": "稳健载重建议",
  "detail": "按路线和架型保留验证组，对台架突刺稳健估计载重趋势，签认后给派车应用。",
  "path": "/load_advisories",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "truck",
      "label": "参照车架"
    },
    {
      "name": "route",
      "label": "场内路线"
    },
    {
      "name": "cycle",
      "label": "适用班次"
    },
    {
      "name": "rms_goal",
      "label": "合作社试车指标"
    },
    {
      "name": "ceiling_kg",
      "label": "建议装载上限 kg"
    },
    {
      "name": "slope",
      "label": "Theil–Sen 载重斜率"
    },
    {
      "name": "validation_mae",
      "label": "末段验证 MAE"
    },
    {
      "name": "exclusion_count",
      "label": "异动残差数"
    },
    {
      "name": "evidence_span",
      "label": "训练重量区间 kg"
    },
    {
      "name": "token",
      "label": "计算凭证"
    }
  ],
  "layout": "flip",
  "view": "table",
  "actions": [
    {
      "name": "fit_load",
      "label": "计算稳健载重建议",
      "path": "/load_advisories/fit-load",
      "fields": [
        {
          "name": "truck",
          "label": "参照车架",
          "kind": "text",
          "initial": "TRUCK-23"
        },
        {
          "name": "route",
          "label": "场内路线",
          "kind": "text",
          "initial": "EAST-REEF"
        },
        {
          "name": "cycle",
          "label": "适用班次",
          "kind": "text",
          "initial": "PM-02"
        },
        {
          "name": "rms_goal",
          "label": "试车指标",
          "kind": "float",
          "initial": 0.92
        }
      ],
      "help": "同一路线和架型按载重分层留出，试车上限约束建议范围。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "confirm_load",
      "label": "签认载重建议",
      "path": "/load_advisories/confirm-load",
      "fields": [
        {
          "name": "code",
          "label": "签认建议号",
          "kind": "text",
          "initial": "AD-QA"
        },
        {
          "name": "token",
          "label": "计算凭证",
          "kind": "token",
          "initial": ""
        }
      ],
      "help": "签认将模型范围、误差与当班用途固化。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "load_advisories";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
