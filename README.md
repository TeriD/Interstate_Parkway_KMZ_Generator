# Interstate_Parkway_KMZ File Generator
There are currently multiple versions of conversions from ESRI SDE feature classes to KMZs.  They vary in details by the team who requested the process and the end point locations requested for file deliverables. This repository combines requests from Danny Rogers in Aviation for Foreflight and Andre Johannes in Highway Design.

## Description
Many units within KYTC ustilize Google maps when travelling to remote sites or for other purposes in 3rd party software packages.  To facilitate the display of current KYTC spatial data, conversion of road networks, milepoints, bridge data and some boundary datasets are needed.  These conversions are made to produce pre-defined symbology that are more readable in Google maps with little to no additional effort for the customer.  To date, these are the different flavors of the KMZ generator processes and their frequency:
1.	Aviation ForeFlight KMZs (monthly)
    * represent County and District boundaries to be visible when used within ForeFlight software.
2.	Highway Design KMZs (weekly)
    * represent Interstate and Parkway milepoints to be visible when used within Google Earth software.
3.  Bridge KMZs (weekly)
    * represent Bridge locations and attributes to be visible when used within Google Earth software by bridge inspectors.


## Dependencies
*   Python
*   ArcGIS Pro 3.1.x or higher
*   Python modules
    - arcpy
    - json
    - logging
    - datetime
    - os (path)
    - shutil (copytree, ignore_patterns)
    - smtplib
    - subprocess
    - sys
    - traceback

## Installing & Operation
*  This process script runs as a scheduled task on the PRD SDE server (KTC1PP-SNGI001A), using the kytc\gis.autoprocessprod account, which has access to the shared folder on N:\Everyone\GIS.  The operational script to produce these KMzs is located in the following directory:
    
    - ...D:\Scripts\Internal_Tasks\Interstate_Pkwy_MM_KMZs\Interstate_Parkway_KMZGenerator.py

The process retrieves a list of all layerfiles in a subfolder to define the symbology for each feature class for the KMZs to be generated.  These layerfiles are located in the following directory:

    - ...D:\Scripts\Internal_Tasks\Interstate_Pkwy_MM_KMZs\LayerFiles

The layerfiles are converted to KMZs using the arcpy module.  The KMZs are first written to a local transfer and then copied to the shared directory:

    - ...N:\Everyone\GIS\KMZs\Interstate_Parkway_KMZs

The process runs on a weekly basis after the HIS Extracts have completed.
# Interstate_Parkway_KMZ_Generator
