# Gyroflow to CSV

Convert your [Gyroflow](https://gyroflow.xyz) stabilization to a CSV file.
Make sure to choose "including processed gyro data" when exporting from Gyroflow.
As default it saves out the rotations as Euler rotation (ZYX).
It also saves out the data in your footages' native frame rate.

## CLI Script

```
positional arguments:
  gyroflow_path         The path to your Gyroflow file

optional arguments:
  -h, --help            show this help message and exit
  -s, --smoothed        Calculate from smoothed quaternions
  -q, --quaternions     Save data as quaternions
  -a, --all_timestamps  Save all timestamps instead of FPS converted
```

You can later use the [Vonk](https://docs.google.com/document/d/1U9WfdHlE1AZHdU6_ZQCB1I2nSa5I7TyHG2vKMi2I7v8/edit?usp=sharing) data nodes inside of Fusion (you find it in Reactor) to read the CSV and drive a 3D camera with it. Download the example project if you want to see how it's done.

## Resolve/Fusion Integration Script

Inside the "Atoms/com.JacobDanell.GyroflowFusion/" folder are the files for a Resolve/Fusion GUI based Gyroflow integration script. This is a snapshot of the files that will be included in a future "Reactor Package Manager" distributed atom package.

### Install Notes

Step 1. Copy the "Scripts/Comp/Gyroflow Fusion/" folder to "Reactor:/Deploy/Scripts/Comp/Gyroflow Fusion/".

Step 2. Copy the "Macros/Gyroflow Fusion/" folder to "Reactor:/Deploy/Macros/Gyroflow Fusion/".

Step 3. Copy the "Docs/Gyroflow Fusion/" folder to "Reactor:/Deploy/Docs/Gyroflow Fusion/".

Step 4. Copy the "Comp/Gyroflow Fusion/" folder to "Reactor:/Deploy/Comp/Gyroflow Fusion/".

Step 5. Copy the file "Config/DragDrop/Gyroflow Fusion DragDrop.fu" folder to "Reactor:/Deploy/Config/DragDrop/". You might have to manually create the "DragDrop" folder if it does not exist at the destination location.

Step 6. Use the Resolve/Fusion based "Reactor Package Manager" to install the "Vonk Ultra" package.

Step 7. Read the markdown formatted documentation provided at "Reactor:/Deploy/Docs/Gyroflow Fusion/README.md" for usage instructions.
