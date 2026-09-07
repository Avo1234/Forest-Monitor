import ee
import json
from datetime import datetime, timedelta

# Initialize Earth Engine
ee.Initialize(project='project-b4195de3-1a22-4a8b-a89')

def run_weekly_deforestation_job():
    today = datetime.utcnow().date()
    # Past 7 days (current week) vs the prior 7 days (baseline week)
    t_curr_end = today
    t_curr_start = today - timedelta(days=7)
    t_prev_start = t_curr_start - timedelta(days=7)

    print(f"Executing weekly job: {t_curr_start} to {t_curr_end} vs baseline {t_prev_start}")

    # Monitored AOI (Eastern Region / Southern Ghana Reserve)
    aoi = ee.Geometry.Polygon([[
        [-1.0200, 5.9000],
        [-0.9500, 5.9000],
        [-0.9500, 5.9550],
        [-1.0200, 5.9550],
        [-1.0200, 5.9000]
    ]])

    # Load ASCENDING Sentinel-1 SAR collections
    def get_weekly_composite(start_d, end_d):
        col = (
            ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(aoi)
            .filterDate(start_d.strftime('%Y-%m-%d'), end_d.strftime('%Y-%m-%d'))
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
            .select('VH')
        )
        return col.median().focal_median(radius=1.5, units='pixels').clip(aoi)

    prev_img = get_weekly_composite(t_prev_start, t_curr_start)
    curr_img = get_weekly_composite(t_curr_start, t_curr_end)

    # Difference in decibels
    delta_vh = curr_img.subtract(prev_img)
    deforestation = delta_vh.lte(-3.0)  # > 3 dB backscatter loss

    # Remove isolated pixels (min 4 connected pixels)
    connected = deforestation.connectedPixelCount(10, True)
    clean_mask = deforestation.updateMask(connected.gte(4))

    # Convert raster clusters to vector polygons for the web dashboard
    vectors = clean_mask.reduceToVectors(
        geometry=aoi,
        scale=10,
        geometryType='polygon',
        eightConnected=True,
        maxPixels=1e8
    )

    # Export to local GeoJSON
    geojson_data = vectors.getInfo()
    filename = f"deforestation_week_{today.strftime('%Y_W%W')}.geojson"
    with open(filename, 'w') as f:
        json.dump(geojson_data, f)

    print(f"Saved weekly vector alerts to {filename}")

if __name__ == '__main__':
    run_weekly_deforestation_job()