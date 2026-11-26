# 山地苗圃运苗车载重减振

岭雨苗木运输合作社的场内苗盘装车单。工作人员按架型称重、比较路线台架震动，并复核固定带后调度苗木车。

## 现场工作与联系人

模拟客户为岭雨苗木运输合作社。苗盘检尺、路线颠簸批、载重趋势、限载调度；架型固定带未检禁止派车。

- 车架与固定凭证 `truck_racks`，字段为 `rack_type`（架型）、`bay_count`（苗盘槽数）、`workshop_kg`（内部试车重量上限 kg）、`strap_mark`（本次检测凭证）、`strap_cycle`（当前检验班次）、`inspection`（检测状态）。模型约束位于 `backend/domain/truck_racks_model.py`，规则位于 `truck_racks_service.py`。
- 苗盘检尺 `plant_trays`，字段为 `rack_type`（适配架型）、`plants`（苗圃批名）、`trays`（盘数）、`tare_kg`（单盘皮重 kg）、`stock_kg`（单盘净重 kg）、`gross_kg`（总毛重 kg）、`stage`（备车状态）。模型约束位于 `backend/domain/plant_trays_model.py`，规则位于 `plant_trays_service.py`。
- 路段与振动簿 `road_observations`，字段为 `route`（场内路线）、`rack_type`（观测架型）、`load_kg`（实测载重 kg）、`rms`（台架 RMS 指标）、`sensor_ref`（试车记录号）、`verified`（数据复核）。模型约束位于 `backend/domain/road_observations_model.py`，规则位于 `road_observations_service.py`。
- 稳健载重建议 `load_advisories`，字段为 `truck`（参照车架）、`route`（场内路线）、`cycle`（适用班次）、`rms_goal`（合作社试车指标）、`ceiling_kg`（建议装载上限 kg）、`slope`/`intercept`（Theil–Sen 载重斜率与截距凭据）、`validation_mae`（留出 MAE）、`baseline_mae`（同一批留出上的现行建议 MAE）、`exclusion_count`（异动残差数）、`evidence_span`（训练重量区间 kg）、`holdout_codes`（复核员选定的同一批留出记录）、`based_on`/`replaces`（原建议）、`version` 与 `current`/`is_current`（版本和现行指针）、`token`（计算凭证）。模型约束位于 `backend/domain/load_advisories_model.py`，规则位于 `load_advisories_service.py`。
- 派车与卸苗回单 `haul_dispatches`，字段为 `truck`（车架）、`advisory`（签认建议）、`lot`（苗盘批号）、`strap_snapshot`（派车时固定带凭证）、`stage`（作业状态）、`receipt`（对方签收号）。模型约束位于 `backend/domain/haul_dispatches_model.py`，规则位于 `haul_dispatches_service.py`。

团队为模拟的12 人运输班，按车架和路线安排出圃苗盘。

装车单、路况口述和固定带复检由三个人分别记录。雨后颠簸读数拖偏平均值，车架换带容易漏验，限载纸条难反查到原苗盘批次。

上游是苗盘检尺和运输颠簸读数，司机签收限载调度和固定带核对凭证。

### 一天的业务操作

1. 07:40 从检尺记录读取香樟 LOT-QA 的 5 盘净重，每盘另加 2 kg 皮重，毛重 95 kg。
2. 08:20 从 EAST-REEF 模拟场内路线导入 SENS-QA，复核架型、称重和 RMS。
3. 09:10 在签认席对 TRUCK-23 复核模型斜率和留出误差，给 PM-02 班留下一条建议。
4. 10:00 尝试派车，发现固定带凭证处于待检；拒绝后苗盘仍可继续编排。
5. 10:30 负责人按横抽盘架为 PM-02 班签入 STRAP-23-PM02，验证超重苗盘仍不得派出。
6. 13:00 派出 95 kg 的 LOT-QA 后台架记录锁定。
7. 14:10 验证新撤销凭证禁止下一单；已完成的一趟保留原检测签注。收到 UNLOAD-018 后签回苗盘。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://127.0.0.1:18310`。FastAPI OpenAPI 在 `http://127.0.0.1:19310/docs`。
Compose 运行 Nginx、Python FastAPI、独立 Redis 消费进程、SQL 数据库和 Redis，SQL 与 Redis 使用命名卷。
本机开发时，在 Python 3.11 环境安装 `backend/requirements.txt` 后从 backend 目录运行 `uvicorn core.app:app`。须提供 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，`SEED_DEMO` 控制演示初始化。

| 演示账号 | 权限 |
|---|---|
| operator@demo.test | 提交领域记录和计算请求 |
| reviewer@demo.test | 提交记录并执行有业务约束的复核操作 |
| viewer@demo.test | 浏览业务台账 |

三个本地演示账号均使用 `DemoC0de!2026`。角色在 `backend/core/roles.py` 和 `frontend/src/store.js` 中声明。计算状态在 worker、queueing、API 和同一前端 store 中使用。

## 页面与接口

| 业务任务 | FastAPI 路由 | 页面 |
|---|---|---|
| 车架与固定凭证 | `/truck_racks` /truck_racks/sign-strap，/truck_racks/withdraw-strap | `frontend/src/pages/truck_racks.js` |
| 苗盘检尺 | `/plant_trays` /plant_trays/measure-trays | `frontend/src/pages/plant_trays.js` |
| 路段与振动簿 | `/road_observations` /road_observations/record-run，/road_observations/verify-run，/road_observations/select-holdout | `frontend/src/pages/road_observations.js` |
| 稳健载重建议 | `/load_advisories` /load_advisories/fit-load，/load_advisories/confirm-load，/load_advisories/compare-load，/load_advisories/rebase-load | `frontend/src/pages/load_advisories.js` |
| 派车与卸苗回单 | `/haul_dispatches` /haul_dispatches/plan-dispatch，/haul_dispatches/sign-receipt | `frontend/src/pages/haul_dispatches.js` |

SQL 实体与约束在 `backend/domain` 下维护。前端使用原生 ES modules。核心算子为 TheilSenRegressor。真实算法为 scikit-learn 的 TheilSenRegressor，固定随机种子 1086；未显式选择留出记录时仍按排序后每四条留出一条，工作台传入 `holdout_codes` 后则将该批已复核记录整体留出且不进入训练。换版时用同一批留出记录重算现行建议 MAE，旧建议缺少可复核的拟合凭据则暂停，候选 MAE 严格更低才允许签认；同一车/路线/班次只保留一个现行版本，签认重试按编号或计算凭证幂等返回，并发落后候选按现行建议重算。载重建议仅在已观测训练范围和内部装备基准内插，偏差超稳健残差阈值仅提示核对。

种子为合作社内部模拟，振动与载重建议用于演示数据流程，不提供上路载重、固定带安装或车辆安全标准。当前只支持两个架型和两条模拟路线。撤销固定凭证拒绝后续派车，已出车凭证保留供回签追溯。

[MIT](LICENSE)
