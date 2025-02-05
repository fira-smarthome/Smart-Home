class Room:
    def __init__(self, name, coordinates):
        self.name = name
        self.coordinates = coordinates  # List of (x, y) tuples
        # Precompute bounding box for optimization
        self.min_x = min(x for x, y in coordinates)
        self.max_x = max(x for x, y in coordinates)
        self.min_y = min(y for x, y in coordinates)
        self.max_y = max(y for x, y in coordinates)
        self.percentage = 0.0
        self.area = self._calculate_area()

    def _calculate_area(self):
        """Calculate polygon area using the shoelace formula."""
        x = [p[0] for p in self.coordinates]
        y = [p[1] for p in self.coordinates]
        n = len(x)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += x[i] * y[j]
            area -= x[j] * y[i]
        return abs(area) / 2.0

    def contains_point(self, point):
        px, py = point

        if not (self.min_x <= px <= self.max_x and self.min_y <= py <= self.max_y):
            return False
        inside = False
        num_vertices = len(self.coordinates)
        for i in range(num_vertices):
            x1, y1 = self.coordinates[i]
            x2, y2 = self.coordinates[(i + 1) % num_vertices]
            if (y1 > py) != (y2 > py):
                x_intersect = (py - y1) * (x2 - x1) / (y2 - y1) + x1
                if px < x_intersect:
                    inside = not inside

        return inside

    def __str__(self):
        return str(self.coordinates)


class House:
    def __init__(self):
        self.rooms = []
        self.whole_area = 0

    def add_room(self, room):
        self.rooms.append(room)
        self.whole_area = sum([i.area for i in self.rooms])

    def find_room(self, point) -> Room:
        for room in self.rooms:
            if room.contains_point(point):
                return room
        return None

    def print_room_percentages(self):
        """
        Calculate room area as a percentage of the entire image.
        """
        whole_area = sum([i.area for i in self.rooms])
        return str.join(", ", [f'{i.name}: {i.area / whole_area}' for i in self.rooms])

    def clean(self, delta: float, room: Room):
        room.percentage = room.percentage + delta / (room.area / self.whole_area)

    def rooms_cleaning_percentages(self):
        return [{
            "room": i.name,
            "percentage": i.percentage
        } for i in self.rooms]

    def __str__(self):
        return f"Has {len(self.rooms)} rooms. {[str(i) for i in self.rooms]}"
