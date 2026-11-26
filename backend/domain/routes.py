from domain.truck_racks_api import router as truck_racks
from domain.plant_trays_api import router as plant_trays
from domain.road_observations_api import router as road_observations
from domain.load_advisories_api import router as load_advisories
from domain.haul_dispatches_api import router as haul_dispatches

routers = (truck_racks, plant_trays, road_observations, load_advisories, haul_dispatches,)
