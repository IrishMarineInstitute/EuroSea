from math import atan2, pi

def get_direction(u, v, criteria):
    ''' Get direction of vector from u, v components. Direction expressed
    as degrees clockwise from North. Criteria is either "TO" or "FROM". '''
    
    # Get angle in trigonometric convention [deg] anti-clockwise from EAST
    angle = atan2(v, u) * 180 / pi
    # Convert to clockwise from NORTH
    angle = 90 - angle
    
    # if direction FROM, +180 deg
    if criteria == 'FROM':
        angle += 180
    # Make sure angle is in the [0, 360) interval
    if angle < 0:
        angle += 360
    elif angle >= 360:
        angle -= 360
        
    return angle