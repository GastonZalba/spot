import ept

def export_pointcloud(self, file):
    query = ept.EPT(file)
    las = query.as_laspy()
    print(las)