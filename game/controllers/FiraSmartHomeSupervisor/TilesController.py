import math


class StartTile:
    def __init__(self, min: list, max: list, node, center=None):
        self.min = min
        self.max = max
        self.center = center
        self.tile_node = node


def coordination_to_grid(coordination, supervisor):
    tiles = math.ceil(math.sqrt(supervisor.getFromDef('SURFACE').getField("children").getCount()))

    side = 0.3 * supervisor.getFromDef("START_TILE").getField("xScale").getSFFloat()
    height = supervisor.getFromDef("START_TILE").getField("height").getSFFloat()
    width = supervisor.getFromDef("START_TILE").getField("width").getSFFloat()
    return int(
        round((coordination[0] + (width / 2 * side)) / side, 0)
        * tiles
        + round((coordination[2] + (height / 2 * side)) / side, 0)
    )


def grid_to_coordination(x, z, supervisor):
    side = 0.3 * supervisor.getFromDef("START_TILE").getField("xScale").getSFFloat()

    # coor_x = round((x + side) / side, 0)
    # coor_z = round((z + side) / side, 0)

    coor_x = (x - 1) * side
    coor_z = (z - 1) * side

    return coor_x, coor_z
