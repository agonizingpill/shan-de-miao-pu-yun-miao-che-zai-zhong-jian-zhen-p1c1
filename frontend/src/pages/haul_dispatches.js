        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "限载派车与卸苗回签",
  "module": "派车与卸苗回单",
  "caption": "派车与卸苗回单",
  "detail": "核对签认车架、苗盘毛重和当班固定凭证。派车与苗盘状态在同一事务更新。",
  "path": "/haul_dispatches",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "truck",
      "label": "车架"
    },
    {
      "name": "advisory",
      "label": "签认建议"
    },
    {
      "name": "lot",
      "label": "苗盘批号"
    },
    {
      "name": "strap_snapshot",
      "label": "派车时固定带凭证"
    },
    {
      "name": "stage",
      "label": "作业状态"
    },
    {
      "name": "receipt",
      "label": "对方签收号"
    }
  ],
  "layout": "split",
  "view": "grid",
  "actions": [
    {
      "name": "plan_dispatch",
      "label": "发出合作社派车单",
      "path": "/haul_dispatches/plan-dispatch",
      "fields": [
        {
          "name": "code",
          "label": "派车单号",
          "kind": "text",
          "initial": "RUN-QA"
        },
        {
          "name": "advisory",
          "label": "签认建议号",
          "kind": "text",
          "initial": "AD-QA"
        },
        {
          "name": "lot",
          "label": "苗盘批号",
          "kind": "text",
          "initial": "LOT-QA"
        },
        {
          "name": "truck",
          "label": "计划车架号",
          "kind": "text",
          "initial": "TRUCK-23"
        }
      ],
      "help": "先复检车架，再结合签认建议计算可装盘数。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "sign_receipt",
      "label": "回收卸苗签收凭证",
      "path": "/haul_dispatches/sign-receipt",
      "fields": [
        {
          "name": "dispatch",
          "label": "派车单号",
          "kind": "text",
          "initial": "RUN-QA"
        },
        {
          "name": "receipt",
          "label": "卸苗签收号",
          "kind": "text",
          "initial": "UNLOAD-018"
        }
      ],
      "help": "收回苗圃卸苗回单并完成苗盘交接。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "haul_dispatches";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
