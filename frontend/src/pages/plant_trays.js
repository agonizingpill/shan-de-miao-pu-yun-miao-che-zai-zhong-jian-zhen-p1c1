        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "苗盘检尺与逐盘皮重",
  "module": "苗盘检尺",
  "caption": "苗盘检尺",
  "detail": "清点人员登记容器、皮重和苗木净重。服务端核算装车重量，派车流程消费同一条苗盘记录。",
  "path": "/plant_trays",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "rack_type",
      "label": "适配架型"
    },
    {
      "name": "plants",
      "label": "苗圃批名"
    },
    {
      "name": "trays",
      "label": "盘数"
    },
    {
      "name": "tare_kg",
      "label": "单盘皮重 kg"
    },
    {
      "name": "stock_kg",
      "label": "单盘净重 kg"
    },
    {
      "name": "gross_kg",
      "label": "总毛重 kg"
    },
    {
      "name": "stage",
      "label": "备车状态"
    }
  ],
  "layout": "split",
  "view": "table",
  "actions": [
    {
      "name": "measure_trays",
      "label": "登记苗盘毛重",
      "path": "/plant_trays/measure-trays",
      "fields": [
        {
          "name": "code",
          "label": "苗盘批号",
          "kind": "text",
          "initial": "LOT-QA"
        },
        {
          "name": "plants",
          "label": "苗圃批名",
          "kind": "text",
          "initial": "香樟 8 寸穴盘苗"
        },
        {
          "name": "rack_type",
          "label": "适配架型",
          "kind": "text",
          "initial": "横抽盘架"
        },
        {
          "name": "trays",
          "label": "盘数",
          "kind": "int",
          "initial": 5
        },
        {
          "name": "tare_kg",
          "label": "单盘皮重 kg",
          "kind": "float",
          "initial": 2
        },
        {
          "name": "stock_kg",
          "label": "单盘净重 kg",
          "kind": "float",
          "initial": 17
        }
      ],
      "help": "使用同批次的单盘皮重和净重。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "plant_trays";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
