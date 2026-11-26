        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "车架和固定带复检",
  "module": "车架与固定凭证",
  "caption": "车架与固定凭证",
  "detail": "固定凭证绑定车架、架型和检验班次。车架状态变化须经现场负责人复核签字。",
  "path": "/truck_racks",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "rack_type",
      "label": "架型"
    },
    {
      "name": "bay_count",
      "label": "苗盘槽数"
    },
    {
      "name": "workshop_kg",
      "label": "内部试车重量上限 kg"
    },
    {
      "name": "strap_mark",
      "label": "本次检测凭证"
    },
    {
      "name": "strap_cycle",
      "label": "当前检验班次"
    },
    {
      "name": "inspection",
      "label": "检测状态"
    }
  ],
  "layout": "flip",
  "view": "stack",
  "actions": [
    {
      "name": "sign_strap",
      "label": "签入固定带检测",
      "path": "/truck_racks/sign-strap",
      "fields": [
        {
          "name": "truck",
          "label": "车架号",
          "kind": "text",
          "initial": "TRUCK-23"
        },
        {
          "name": "rack_type",
          "label": "检验架型",
          "kind": "text",
          "initial": "横抽盘架"
        },
        {
          "name": "strap_mark",
          "label": "固定带凭证",
          "kind": "text",
          "initial": "STRAP-23-PM02"
        },
        {
          "name": "cycle",
          "label": "检验班次",
          "kind": "text",
          "initial": "PM-02"
        }
      ],
      "help": "输入现场纸质检测单、对应架型和班次。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "withdraw_strap",
      "label": "撤销固定带见证",
      "path": "/truck_racks/withdraw-strap",
      "fields": [
        {
          "name": "truck",
          "label": "车架号",
          "kind": "text",
          "initial": "TRUCK-23"
        },
        {
          "name": "strap_mark",
          "label": "固定带凭证",
          "kind": "text",
          "initial": "STRAP-23-PM02"
        }
      ],
      "help": "记录发生更换后撤销当前检测凭证。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "truck_racks";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
