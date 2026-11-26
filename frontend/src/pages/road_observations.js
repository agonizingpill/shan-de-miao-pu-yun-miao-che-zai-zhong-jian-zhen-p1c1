        import {workspace} from '../workspace.js';
        import {tracePlot} from '../trace-plot.js';

        const page = {
  "title": "路线试车振动簿",
  "module": "路段与振动簿",
  "caption": "路段与振动簿",
  "detail": "记录内部场地路线、架型、配重和台架 RMS；初录资料经核验后才能进入模型。",
  "path": "/road_observations",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "route",
      "label": "场内路线"
    },
    {
      "name": "rack_type",
      "label": "观测架型"
    },
    {
      "name": "load_kg",
      "label": "实测载重 kg"
    },
    {
      "name": "rms",
      "label": "台架 RMS 指标"
    },
    {
      "name": "sensor_ref",
      "label": "试车记录号"
    },
    {
      "name": "verified",
      "label": "数据复核"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": [
    {
      "name": "record_run",
      "label": "登记路线试车记录",
      "path": "/road_observations/record-run",
      "fields": [
        {
          "name": "code",
          "label": "观察记录",
          "kind": "text",
          "initial": "OBS-QA"
        },
        {
          "name": "route",
          "label": "场内路线",
          "kind": "text",
          "initial": "EAST-REEF"
        },
        {
          "name": "rack_type",
          "label": "观测架型",
          "kind": "text",
          "initial": "横抽盘架"
        },
        {
          "name": "load_kg",
          "label": "载重 kg",
          "kind": "float",
          "initial": 95
        },
        {
          "name": "rms",
          "label": "台架 RMS",
          "kind": "float",
          "initial": 0.71
        },
        {
          "name": "sensor_ref",
          "label": "试车记录号",
          "kind": "text",
          "initial": "SENS-QA"
        }
      ],
      "help": "RMS 指标只来自内部仿真台架。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "verify_run",
      "label": "复核称重与振动记录",
      "path": "/road_observations/verify-run",
      "fields": [
        {
          "name": "observation",
          "label": "观察编号",
          "kind": "text",
          "initial": "OBS-QA"
        }
      ],
      "help": "核对传感器号和配重后再进入训练账。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "road_observations";
        export async function render(root, role) {
          await workspace(root, role, page);
          await tracePlot(root);

        }
