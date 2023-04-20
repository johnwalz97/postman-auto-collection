class FastAPIParser:
    def __init__(self, app):
        self.app = app

    def parse(self):
        routes = self.app.routes
        paths = {}
        for route in routes:
            path = route.path
            if path not in paths:
                paths[path] = {}
            paths[path][route.methods[0]] = route.endpoint
        return paths
