import math
from unitconversion import convert_unit


class PlacementError(Exception):
    pass


def hub_layout(bat_dim, sensors):
    """
    The goal here is to place all of the required components within a hub of the footprint given by hub_size X hub_size.
    Hub size is determined using the sizes of the components required to go on/in the hub.

    In addition, right now I am hard-coding the sizes of the flight controller, receiver, gps, and ESC into this
    function. In the future these sizes can be easily passed in on a call-by-call basis if for instance the user has a
    choice of various ESCs, receivers, etc.

    The input bat_dim is a list defining the size of the battery of the form [xdim, ydim, zdim] in inches.

    The input sensors is a list of sensor objects the user requires to be on the vehicle.
    """

    def is_occupied(this_place, this_size, mode='check'):
        """
        This function takes a starting point on the grid (representing the center of the rectangle placement) and checks
        whether the space that would be occupied by the rectangle centered on that spot is available for occupation.
        If the rectangle would overlap any occupied grid points, or if it would partially lay outside of the grid, the
        function returns True (i.e., the space is occupied). If all points that the rectangle would occupy are within
        the grid and unoccupied, the function returns False.

        The mode input can either be 'check' (default) or 'mark'. If mode is set to 'check', the function will simply
        check whether or not the rectangle defined by 'this_size' can be placed at location 'this_place', returning True
        or False appropriately. If the mode is set to 'mark', the function will mark the grid area defined by a
        rectangle defined by 'this_size' centered at 'this_place' as occupied (i.e., changes all grid point values to
        1). The 'mark' mode should only be used if it has already been established the grid area is clear, because it
        changes the value of the grid points before checking if the entire area is unoccupied.
        """
        l = this_place[2]
        if this_place[3] == 'forward':
            top_row = this_place[0] - int(math.ceil(this_size[0]/2/delta_p))
            bot_row = this_place[0] + int(math.ceil(this_size[0]/2/delta_p))
            left_col = this_place[1] - int(math.ceil(this_size[1]/2/delta_p))
            rght_col = this_place[1] + int(math.ceil(this_size[1]/2/delta_p))
        else:
            top_row = this_place[0] - int(math.ceil(this_size[1]/2/delta_p))
            bot_row = this_place[0] + int(math.ceil(this_size[1]/2/delta_p))
            left_col = this_place[1] - int(math.ceil(this_size[0]/2/delta_p))
            rght_col = this_place[1] + int(math.ceil(this_size[0]/2/delta_p))

        for r in xrange(top_row, bot_row+1):
            for c in xrange(left_col, rght_col+1):
                try:
                    # If grid point is already occupied, return True
                    if grid[l][r][c]:
                        return True
                    elif mode == 'mark':
                        grid[l][r][c] = 1
                # If index is out of the grid, return True.
                except IndexError:
                    return True
        # If no points were occupied or out of the grid, return False
        return False

    def find_place(this_size, pref_layer, layer_req=False, req_orient=None):
        """
        This function finds the place where the rectangle defined by 'this_size' is closest to the center of a
        layer, starting with the preferred layer given by 'pref_layer'. The layers then progress like pref_layer-1 -->
        pref_layer+1 --> pref_layer-2 --> etc. If layer preference changes then this order can be changed. Optimization
        of the layout gets more complicated if one does not place the battery and flight controller in the center of
        layers 1 and 2 (indices 0 and 1) respectively. Weight distributions may also become a consideration if the
        components have significantly different weight/area on the grid.

        The inputs 'in_layer_list' and 'req_orient' are for use when placing sensors which have specific requirements
        for where they are located on/in the hub.
        """
        if pref_layer is None:
            pref_layer = 1
        # First create list of layers to try in order of preference
        layer_list = []
        for l in xrange(n_layers):
            layer_list.append(pref_layer-l)
            if l != 0:
                layer_list.append(pref_layer+l)
        layer_list = [l for l in layer_list if 0 <= l < n_layers]

        if layer_req:
            layer_list = [pref_layer]

        if req_orient is not None:
            orient_list = [req_orient]
        else:
            orient_list = ['forward', 'sideways']

        for current_layer in layer_list:
            for orient in orient_list:
                # We can eliminate many grid points before brute forcing because we know the rectangle cannot lay
                # outside the grid.
                if orient == 'forward':
                    start_row = int(this_size[0]/2/delta_p)
                    end_row = n_points - int(this_size[0]/2/delta_p)
                    start_col = int(this_size[1]/2/delta_p)
                    end_col = n_points - int(this_size[1]/2/delta_p)
                else:
                    start_row = int(this_size[1]/2/delta_p)
                    end_row = n_points - int(this_size[1]/2/delta_p)
                    start_col = int(this_size[0]/2/delta_p)
                    end_col = n_points - int(this_size[0]/2/delta_p)
                all_places = [(r, c, current_layer, orient)
                              for r in xrange(start_row, end_row+1) for c in xrange(start_col, end_col+1)]
                # Rank list based on distance from center
                all_places_ranked = rank_places(all_places)
                # Starting with place closest to center, check is_occupied
                for current_place in all_places_ranked:
                    if not is_occupied(current_place, this_size):
                        return current_place
        return False

    def rank_places(places):
        """
        Rank the available places for the rectangle according to their distance from the center (closeness to the center
        is preferred). I thought this was a simple and good way to achieve the reasonable configuration, without taking
        into account the materials the rectangles are made out of (i.e., the weight distribution resulting from the
        arrangement).
        """
        def dist2center(place):
            return ((place[0]-center)**2 + (place[1]-center)**2)**0.5
        return sorted(places, key=dist2center)

    def find_top_layer(g):
        """
        This function takes in a grid (as defined above) and returns the uppermost layer index containing a
        component(s). It determines if a layer is occupied by computing the number of occupied points minus the number
        of points occupied by arm attachments (an arm_dim X arm_dim square in each layer corner).
        """
        i = len(g) - 1
        for l in reversed(g):
            flat_l = [c for r in l for c in r]
            n_occupied_pts = flat_l.count(1)
            n_corner_pts = 4*(math.ceil(arm_dim/delta_p) + 1)**2
            if n_occupied_pts > n_corner_pts:
                return i
            i -= 1

    #################################################################################################################

    # First define the size of the required electronic components that will go on the hub. Convert to meters.
    bat_size = [convert_unit(d, 'in', 'm') for d in bat_dim]
    fc_size = [convert_unit(d, 'in', 'm') for d in [2.77, 1.77, 0.53]]
    # receiver_size = [convert_unit(d, 'in', 'm') for d in [1.57, 1.06, 0.35]]
    # gps_size = [convert_unit(d, 'in', 'm') for d in [1.49, 1.49, 0.33]]
    # esc_size = [convert_unit(d, 'in', 'm') for d in [2.5, 2.25, 0.325]]

    non_sensor_sizes = [bat_size, fc_size]
    comp_sizes = [bat_size, fc_size]
    interior_sensor_zdims = []
    for sensor in sensors:
        sensor_size = [sensor.xdim['value'], sensor.ydim['value'], sensor.zdim['value']]
        comp_sizes.append(sensor_size)
        if sensor.req_layer is None:
            interior_sensor_zdims.append(sensor_size[2])
    comp_xy_sizes = [size[:2] for size in comp_sizes]

    # Determine the required size of the hub
    arm_dim = 1*0.0254  # Size of corner for arm connections in meters
    flat_comp_xy_sizes = [dim for size in comp_xy_sizes for dim in size]
    max_comp_dim = max(flat_comp_xy_sizes)
    # Start with a guess equal to the maximum component dimension plus a comfort factor. For most cases this will be the
    # battery max dimension and this guess will be the final hub size.
    hub_size = max_comp_dim * 1.05
    # However, it is concievable that a large, squareish component could still not fit in the hub after taking into
    # account the areas for the arm attachments, therefore we check the other components and resize if necessary.
    for size in comp_xy_sizes:
        if all((dim >= (hub_size-2*arm_dim) for dim in size)):
            hub_size = (min(size)+2*arm_dim)*1.05

    # Determine separation between hub layers using maximum z dimension of components, other than sensors that are
    # required to be mounted to the top or bottom of the hub.
    hub_separation = 1.5 * max([size[2] for size in non_sensor_sizes] + interior_sensor_zdims)

    # Create hub grid 101 x 101 x 4. Initialized to zero (all space is unoccupied)
    n_points = 101  # Odd number chosen so there is a center grid point located at (50, 50) in 2D
    n_layers = 4
    grid = [[[0 for i in xrange(n_points)] for j in xrange(n_points)] for k in xrange(n_layers)]
    center = int((n_points-1)/2)    # Or just n_points/2 ehhh..
    delta_p = hub_size/(n_points-1)

    # Mark off space for arms to be connected to the hub. For now these will be 1 inch in each corner per the GT tool.
    for layer in xrange(n_layers):
        for row in xrange(n_points):
            if (hub_size/n_points*row <= arm_dim) or (hub_size/n_points*row > hub_size-arm_dim-delta_p):
                for col in xrange(n_points):
                    if (hub_size/n_points*col <= arm_dim) or (hub_size/n_points*col > hub_size-arm_dim-delta_p):
                        grid[layer][row][col] = 1

    # Place flight controller in the center of layer 1.
    fc_place = [center, center, 0, 'forward']
    is_occupied(fc_place, fc_size, mode='mark')

    # Place battery in the second layer of the grid. In reality this is actually the top of the first layer
    # (or equivalently the bottom of the second layer). In the base configuration the flight controller will be mounted
    # to the floor of the first layer, and the battery will be mounted to the roof of the layer above. The format for
    # the place lists are as follows:
    # bat_place = [row_index, column_index, layer_index, orientation] location of center of component
    # Orientation refers to the direction of the longest dimension.
    bat_place = [center, center, 1, 'forward']
    is_occupied(bat_place, bat_size, mode='mark')

    # Now place all of the sensors the user has selected. If the sensor has a required layer the logic checks to see if
    # that layer is available. If the layer is not available, the alternative will fail. Currently only one sensor can
    # be on the top and bottom layers. This is because I am assuming that the sensor will need a full 360 deg view which
    # could be impeded by allowing more than one sensor on the top or bottom layer.
    for sensor in sensors:
        sensor_size = [sensor.xdim['value'], sensor.ydim['value'], sensor.zdim['value']]
        top_layer = find_top_layer(grid)
        if sensor.req_layer == 'top':
            if top_layer < n_layers-1:
                sensor_req_layer = top_layer + 1
                layer_required = True
            else:
                raise PlacementError("Could not place %s on top layer of hub. Top layer filled." % sensor.name)
        elif sensor.req_layer == 'bottom':
            if top_layer < n_layers-1:
                grid.insert(0, grid.pop())
                sensor_req_layer = 0
                layer_required = True
            else:
                raise PlacementError("Could not place %s on bottom layer of hub. All layers filled" % sensor.name)
        else:
            sensor_req_layer = None
            layer_required = False
        sensor_req_orient = sensor.req_orient
        sensor_place = find_place(sensor_size, sensor_req_layer, layer_required, sensor_req_orient)
        if not sensor_place:
            raise PlacementError("Could not place %s on hub." % sensor.name)
        is_occupied(sensor_place, sensor_size, mode='mark')

    # Return the hub size (in inches), the hub separation (in inches) and the grid, trimming unoccupied layers.
    current_top_layer = find_top_layer(grid)
    return convert_unit(hub_size, 'm', 'in'), convert_unit(hub_separation, 'm', 'in'), grid[:current_top_layer+1]


def hub_layout_simple(bat_dim, sensors):
    # Define battery and flight controller size. It has been determined that other electronic components such as the
    # GPS and receiver will not go on the hub.
    bat_size = [convert_unit(d, 'in', 'm') for d in bat_dim]
    fc_size = [convert_unit(d, 'in', 'm') for d in [2.77, 1.77, 0.53]]

    comp_sizes = [bat_size, fc_size]
    interior_sensor_zdims = []
    for sensor in sensors:
        sensor_size = [sensor.xdim['value'], sensor.ydim['value'], sensor.zdim['value']]
        comp_sizes.append(sensor_size)
        if sensor.req_layer is None:
            interior_sensor_zdims.append(sensor_size[2])
    comp_xy_sizes = [size[:2] for size in comp_sizes]

    # Determine the required size of the hub
    arm_dim = 1*0.0254  # Size of corner for arm connections in meters
    flat_comp_xy_sizes = [dim for size in comp_xy_sizes for dim in size]
    max_comp_dim = max(flat_comp_xy_sizes)
    # Start with a guess equal to the maximum component dimension plus a comfort factor. For most cases this will be the
    # battery max dimension and this guess will be the final hub size.
    hub_size = max_comp_dim * 1.05
    # However, it is concievable that a large, squareish component could still not fit in the hub after taking into
    # account the areas for the arm attachments, therefore we check the other components and resize if necessary.
    for size in comp_xy_sizes:
        if all((dim >= (hub_size-2*arm_dim) for dim in size)):
            hub_size = (min(size)+2*arm_dim)*1.05

    # Determine separation between hub layers. Since in the simplified hublayout model the battery will be placed on the
    # "ceiling" of the layer on which the flight controller is placed, the spacing needs to be at least equal to the
    # sum of their heights with some extra room built in.
    try:
        hub_separation = 1.5 * max((bat_size[2]+fc_size[2]), max(interior_sensor_zdims))
    except ValueError:
        hub_separation = 1.5 * (bat_size[2]+fc_size[2])

    # Since this is a simplifed version of the hublayout code, we will not try to create a grid showing the placement
    # of the components. In order to let the caller know how many layers there are (for use in figuring out the weight
    # of the aircraft) the "grid" is returned as a length 2 list. This is a workaround since the way the caller checks
    # how many layers there are is by checking the length of the grid list of lists returned from this function. This
    # will result in the code sizing the aircraft for a hub with two layers, which

    return convert_unit(hub_size, 'm', 'in'), convert_unit(hub_separation, 'm', 'in'), [None, None]
