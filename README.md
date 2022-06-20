# Gyroflow to CSV

Convert your Gyroflow stabilization to a CSV file.
Make sure to choose "including processed gyro data" when exporting from Gyroflow.
As default it saves out the rotations as Euler rotation (ZYX).
It also saves out the data for your footages FPS

```
positional arguments:
  gyroflow_path         The path to your Gyroflow file

optional arguments:
  -h, --help            show this help message and exit
  -s, --smoothed        Calculate from smoothed quaternions
  -q, --quaternions     Save data as quaternions
  -a, --all_timestamps  Save all timestamps instead of FPS converted
```

You can later use the Vonk inside of Fusion (you find it in Reactor) to read the CSV and drive a 3D camera with it.
Download the example project if you want to see how it's done.