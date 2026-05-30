
# ROS2 Nav2 Assignment — `testbed_navigation`
### ERIC Robotics  |  Testbed-T1.0.0

---

**Candidate:** Amogh Joshi
**Phone:** +91 9607062201
**Email:** [amoghjoshi227@gmail.com](mailto:amoghjoshi227@gmail.com)
**LinkedIn:** [linkedin.com/in/amogh-joshi-83205a36b](https://www.linkedin.com/in/amogh-joshi-83205a36b?utm_source=share_via&utm_content=profile&utm_medium=member_android)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository Structure](#2-repository-structure)
3. [Prerequisites](#3-prerequisites)
4. [Quick Start](#4-quick-start)
5. [Package Architecture](#5-package-architecture)
6. [Launch Files — Detailed Guide](#6-launch-files--detailed-guide)
   - [map_loader.launch.py](#61-map_loaderlaunchpy)
   - [localization.launch.py](#62-localizationlaunchpy)
   - [navigation.launch.py](#63-navigationlaunchpy)
7. [Configuration Files](#7-configuration-files)
   - [amcl_params.yaml](#71-amcl_paramsyaml)
   - [nav2_params.yaml](#72-nav2_paramsyaml)
8. [Plugin Selection & Rationale](#8-plugin-selection--rationale)
9. [Running Step-by-Step](#9-running-step-by-step)
10. [Sending Navigation Goals](#10-sending-navigation-goals)
11. [Tuning Guide](#11-tuning-guide)
12. [Challenges & Solutions](#12-challenges--solutions)
13. [Contact](#13-contact)

---

## 1. Overview

This package, `testbed_navigation`, implements a **fully modular, manually composed** ROS2 navigation stack for the Testbed-T1.0.0 robot without relying on the monolithic `nav2_bringup` launch umbrella.

Each navigation concern is isolated into its own launch file:

| Launch file | Responsibility |
|---|---|
| `map_loader.launch.py` | Load and serve an occupancy-grid map |
| `localization.launch.py` | AMCL-based Monte-Carlo localisation |
| `navigation.launch.py` | Full nav2 stack (planning, control, recovery, BT) |

This design lets each component be developed, tested, and replaced independently — which is exactly what the nav2 plugin architecture is built for.

---

## 2. Repository Structure

```
ros_nav2_assignment/
├── testbed_description/        # Robot URDF, meshes, sensors
├── testbed_gazebo/             # Gazebo world, models, launch
├── testbed_bringup/
│   ├── launch/                 # Full simulation bringup
│   └── maps/
│       └── testbed_world.yaml  # Pre-built occupancy-grid map
└── testbed_navigation/         # ← THIS PACKAGE
    ├── CMakeLists.txt
    ├── package.xml
    ├── config/
    │   ├── amcl_params.yaml    # AMCL particle-filter config
    │   └── nav2_params.yaml    # All nav2 node parameters
    ├── launch/
    │   ├── map_loader.launch.py
    │   ├── localization.launch.py
    │   └── navigation.launch.py
    ├── rviz/
    │   └── nav2_default_view.rviz
    └── scripts/
        └── send_goal.py        # CLI helper to send nav goals
```

---

## 3. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Ubuntu | 22.04 LTS | Required for Humble |
| ROS2 | Humble Hawksbill | [Install guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) |
| Gazebo | 11.10.2 | `sudo apt install gazebo` |
| Nav2 | Humble | `sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup` |
| colcon | latest | `sudo apt install python3-colcon-common-extensions` |

Install all nav2 dependencies at once:

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup \
                 ros-humble-slam-toolbox ros-humble-robot-localization
```

---

## 4. Quick Start

```bash
# 1. Create workspace and clone
mkdir -p ~/assignment_ws/src
cd ~/assignment_ws/src
git clone <your-repository-url>

# 2. Install ROS dependencies
cd ~/assignment_ws
rosdep install --from-paths src --ignore-src -r -y

# 3. Build
colcon build --symlink-install
source install/setup.bash

# 4. Start Gazebo + robot (Terminal 1)
ros2 launch testbed_bringup testbed_full_bringup.launch.py

# 5. Start navigation stack (Terminal 2)
ros2 launch testbed_navigation navigation.launch.py

# 6. Set initial pose in Rviz2, then send a goal
ros2 run testbed_navigation send_goal.py -- 2.0 1.5 0.0
```

---

## 5. Package Architecture

The diagram below shows how data flows through the navigation stack:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Sensor / TF Layer                            │
│   Gazebo ──► /scan (LaserScan)   /odom (Odometry)   /tf /tf_static │
└────────────────────────┬────────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │        map_server           │  ◄── testbed_world.yaml
          │   publishes /map topic      │
          └──────────────┬──────────────┘
                         │ /map
          ┌──────────────▼──────────────┐
          │           amcl              │  ◄── amcl_params.yaml
          │   map → odom TF broadcast   │
          │   /amcl_pose, /particlecloud│
          └──────────────┬──────────────┘
                         │ map→odom TF
          ┌──────────────▼──────────────────────────────┐
          │              bt_navigator                    │
          │   NavigateToPose / NavigateThroughPoses     │
          │   Behaviour-tree orchestration              │
          └───────────┬─────────────────┬───────────────┘
                      │                 │
          ┌───────────▼────┐   ┌────────▼────────────┐
          │  planner_server│   │  controller_server  │
          │  NavFn/Dijkstra│   │  DWB local planner  │
          │  → /plan path  │   │  → cmd_vel_nav      │
          └────────────────┘   └────────┬────────────┘
                                        │
                             ┌──────────▼──────────────┐
                             │   velocity_smoother      │
                             │   → cmd_vel_smoothed    │
                             └──────────┬──────────────┘
                                        │
                             ┌──────────▼──────────────┐
                             │   collision_monitor      │
                             │   → /cmd_vel (final)    │
                             └──────────┬──────────────┘
                                        │
                             ┌──────────▼──────────────┐
                             │   Gazebo diff-drive      │
                             │   plugin / robot HW      │
                             └─────────────────────────┘
```

All lifecycle nodes are managed by a single **`lifecycle_manager`** which handles the `configure → activate` state machine automatically.

---

## 6. Launch Files — Detailed Guide

### 6.1 `map_loader.launch.py`

**Purpose:** Standalone map-serving. Useful when you need the map available (e.g. for mapping or visualisation) without running localisation.

**Key actions:**
- Starts `nav2_map_server/map_server` as a lifecycle node.
- Starts `nav2_lifecycle_manager/lifecycle_manager` to auto-activate it.
- Publishes `/map` (OccupancyGrid) and `/map_metadata`.

**Launch arguments:**

| Argument | Default | Description |
|---|---|---|
| `map_file` | `testbed_bringup/maps/testbed_world.yaml` | Path to map YAML |
| `use_sim_time` | `true` | Use Gazebo clock |
| `autostart` | `true` | Auto-activate lifecycle nodes |

```bash
# Default
ros2 launch testbed_navigation map_loader.launch.py

# Custom map
ros2 launch testbed_navigation map_loader.launch.py \
    map_file:=/home/user/my_map.yaml
```

**Verify in Rviz2:** Add a `Map` display → Topic: `/map`. You should see the testbed occupancy grid.

---

### 6.2 `localization.launch.py`

**Purpose:** Runs map_server + AMCL together — everything needed for localisation without navigation.

**Key actions:**
- Starts `map_server` (same as above).
- Starts `nav2_amcl/amcl` as a lifecycle node with `amcl_params.yaml`.
- Starts a `lifecycle_manager` that activates `map_server` first, then `amcl`.

**Launch arguments:**

| Argument | Default | Description |
|---|---|---|
| `map_file` | `testbed_bringup/maps/testbed_world.yaml` | Path to map YAML |
| `amcl_params_file` | `config/amcl_params.yaml` | Path to AMCL params |
| `use_sim_time` | `true` | Gazebo clock |
| `autostart` | `true` | Auto-activate |

```bash
ros2 launch testbed_navigation localization.launch.py
```

**Verify in Rviz2:**
1. Set fixed frame to `map`.
2. Add `PoseWithCovariance` → `/amcl_pose`.
3. Add `MarkerArray` → `/particlecloud`.
4. Use **2D Pose Estimate** tool to set the initial pose. Particles should converge as the robot moves.

---

### 6.3 `navigation.launch.py`

**Purpose:** Full navigation stack. Includes everything from localization.launch.py plus planning, control, recovery behaviours, velocity smoothing, and collision monitoring.

**Key actions:**
1. Starts all nodes listed in [§5](#5-package-architecture).
2. `lifecycle_manager` activates them in dependency order.
3. Optionally opens Rviz2 with pre-configured navigation view.

**Launch arguments:**

| Argument | Default | Description |
|---|---|---|
| `map_file` | `testbed_world.yaml` | Map path |
| `params_file` | `config/nav2_params.yaml` | Nav2 params |
| `default_bt_xml_filename` | nav2 default BT | Behaviour tree XML |
| `use_sim_time` | `true` | Gazebo clock |
| `autostart` | `true` | Auto-activate |
| `use_rviz` | `true` | Launch Rviz2 |
| `rviz_config_file` | `rviz/nav2_default_view.rviz` | Rviz config |

```bash
# Full stack with Rviz2
ros2 launch testbed_navigation navigation.launch.py

# Headless (CI/testing)
ros2 launch testbed_navigation navigation.launch.py use_rviz:=false
```

---

## 7. Configuration Files

### 7.1 `amcl_params.yaml`

Key parameters and the reasoning behind chosen values:

| Parameter | Value | Rationale |
|---|---|---|
| `min_particles` | 500 | Enough particles for a room-scale environment |
| `max_particles` | 2000 | Upper bound; capped to keep CPU usage reasonable |
| `robot_model_type` | `DifferentialMotionModel` | Testbed-T1.0.0 is differential-drive |
| `laser_model_type` | `likelihood_field` | Faster than beam model, accurate for planar LiDAR |
| `max_beams` | 60 | 60 evenly-spaced beams from a 360° LiDAR |
| `update_min_d` | 0.20 m | Only update filter when robot has moved ≥ 20 cm |
| `update_min_a` | 0.30 rad | Only update filter when robot has rotated ≥ 17° |
| `alpha1–4` | 0.2 each | Balanced odometry noise model |

### 7.2 `nav2_params.yaml`

**Global planner — NavFn (Dijkstra)**

NavFn was chosen over Smac Planner for simplicity and reliability in a well-mapped static environment. `use_astar: false` runs Dijkstra (guaranteed optimal path). `allow_unknown: true` allows the robot to plan through unobserved areas.

**Local planner — DWB (Dynamic Window Approach)**

DWB was chosen because it:
- Handles differential-drive kinematic constraints natively.
- Provides configurable critic weights for smooth, collision-free motion.
- Has excellent Rviz visualisation of sampled trajectories.

Key DWB values tuned for Testbed-T1.0.0:

| Parameter | Value | Notes |
|---|---|---|
| `max_vel_x` | 0.26 m/s | Conservative; safe for indoor nav |
| `max_vel_theta` | 1.0 rad/s | ~57°/s; prevents overshoot |
| `sim_time` | 1.7 s | Projects trajectories 1.7 seconds ahead |
| `vx_samples` | 20 | Adequate sampling density |

**Recovery behaviours:**

| Plugin | Trigger |
|---|---|
| `BackUp` | Robot is stuck; reverses 15 cm |
| `Spin` | Stuck after backup; rotates 360° to re-localise |
| `Wait` | Transient obstacle blocking path; waits 5 s |

---

## 8. Plugin Selection & Rationale

| Component | Plugin chosen | Why |
|---|---|---|
| **Map server** | `nav2_map_server` | Official nav2 plugin; lifecycle-managed |
| **Localisation** | `nav2_amcl` (AMCL) | Proven particle-filter MCL; excellent for known maps |
| **Global planner** | `nav2_navfn_planner/NavfnPlanner` | Simple, reliable, well-tested Dijkstra/A* |
| **Local planner** | `dwb_core::DWBLocalPlanner` | Handles diff-drive; rich trajectory visualisation |
| **BT navigator** | `nav2_bt_navigator` | Standard nav2 action interface; composable BTs |
| **Recovery** | Spin, BackUp, Wait | Handles the three most common stuck scenarios |
| **Path smoother** | `nav2_smoother::SimpleSmoother` | Removes sharp corners from NavFn output |
| **Velocity smoother** | `nav2_velocity_smoother` | Prevents jerky motor commands |
| **Collision monitor** | `nav2_collision_monitor` | Emergency stop layer independent of costmaps |

The architecture was kept deliberately lightweight — no SLAM (pre-built map is provided), no GPS, no 3-D costmaps — matching the assignment's requirement for "basic navigational functionality."

---

## 9. Running Step-by-Step

### Terminal 1 — Gazebo simulation

```bash
source ~/assignment_ws/install/setup.bash
ros2 launch testbed_bringup testbed_full_bringup.launch.py
```

Wait until Gazebo has fully loaded and you see the Testbed robot in the world.

### Terminal 2 — Navigation stack

```bash
source ~/assignment_ws/install/setup.bash
ros2 launch testbed_navigation navigation.launch.py
```

You should see lifecycle transitions in the terminal:

```
[lifecycle_manager_navigation] Configuring map_server
[lifecycle_manager_navigation] Configuring amcl
[lifecycle_manager_navigation] Configuring controller_server
...
[lifecycle_manager_navigation] All nodes activated.
```

### Terminal 3 — Set initial pose (alternative to Rviz)

```bash
source ~/assignment_ws/install/setup.bash
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  '{header: {frame_id: "map"}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0},
  orientation: {w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,...]}}'
```

Or use the **2D Pose Estimate** button in Rviz2 — this is much easier.

### Verify localisation

- In Rviz2, the `/particlecloud` markers should cluster around the robot.
- The `/amcl_pose` arrow should track the robot's position in the map.
- Move the robot in Gazebo (or teleoperate it) and watch the particles converge.

### Send a navigation goal

```bash
# Via Rviz2: use the "Nav2 Goal" button and click on the map

# Via CLI:
ros2 run testbed_navigation send_goal.py -- 2.0 1.5 0.0
```

---

## 10. Sending Navigation Goals

### Option A — Rviz2 (recommended for interactive use)

1. Open Rviz2 (auto-launched with `navigation.launch.py`).
2. Click the **Nav2 Goal** button in the toolbar.
3. Click and drag on the map to set position and heading.

### Option B — CLI helper script

```bash
# Syntax: send_goal.py -- <x> <y> [yaw]
ros2 run testbed_navigation send_goal.py -- 1.5 2.0 1.57

# With a label
ros2 run testbed_navigation send_goal.py -- 3.0 0.5 0.0 --name "Desk area"
```

### Option C — Direct action call

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 1.0, z: 0.0},
  orientation: {z: 0.0, w: 1.0}}}}'
```

### Waypoint following

```bash
ros2 action send_goal /follow_waypoints nav2_msgs/action/FollowWaypoints \
  '{poses: [
    {header: {frame_id: "map"}, pose: {position: {x: 1.0, y: 0.0}, orientation: {w: 1.0}}},
    {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 1.0}, orientation: {w: 1.0}}},
    {header: {frame_id: "map"}, pose: {position: {x: 0.0, y: 0.0}, orientation: {w: 1.0}}}
  ]}'
```

---

## 11. Tuning Guide

### Robot does not reach the goal / oscillates

- Increase `xy_goal_tolerance` and `yaw_goal_tolerance` in `nav2_params.yaml`.
- Reduce `max_vel_x` if the robot overshoots.

### AMCL particles do not converge

- Increase `max_particles` to 3000–5000.
- Ensure the scan topic name in `amcl_params.yaml` matches your URDF (`scan` by default).
- Use the **2D Pose Estimate** tool to give AMCL a better starting hint.

### Robot drives into obstacles

- Increase `inflation_radius` in both costmaps.
- Decrease `cost_scaling_factor` (makes the inflation zone wider / more aggressive).
- Check that `robot_radius` matches the actual robot footprint.

### "Planner failed" error

- Set `allow_unknown: true` in the NavFn planner parameters.
- Widen `tolerance` from 0.5 to 1.0 metres.

### Navigation is too slow

- Increase `max_vel_x` (e.g. 0.5 m/s for open spaces).
- Reduce `sim_time` for DWB (e.g. 1.2 s) for faster trajectory sampling.

---

## 12. Challenges & Solutions

### Challenge 1 — Lifecycle ordering

**Problem:** AMCL would fail to receive the map because it was activated before `map_server` finished publishing.

**Solution:** The `lifecycle_manager` node_names list is ordered: `map_server` appears first, so it reaches `ACTIVE` state before AMCL is configured. The `map_server` is configured with `Transient Local` QoS durability so late subscribers receive the last published map.

---

### Challenge 2 — cmd_vel topic routing with multiple middleware nodes

**Problem:** Three nodes need to touch `cmd_vel`: the controller outputs it, the velocity smoother filters it, and the collision monitor gates it before it reaches Gazebo. Using the same topic name causes conflicts.

**Solution:** A pipeline of renamed topics:
```
controller_server → cmd_vel_nav
velocity_smoother → cmd_vel_smoothed
collision_monitor → cmd_vel  (final, consumed by Gazebo plugin)
```
Each node's topic remapping is declared explicitly in `navigation.launch.py`.

---

### Challenge 3 — AMCL frame ID mismatch

**Problem:** The robot's URDF used `base_link` as the base frame, but AMCL defaulted to `base_footprint`, causing TF lookup failures.

**Solution:** Explicitly set `base_frame_id: "base_footprint"` in `amcl_params.yaml` (or `base_link` if that is what the URDF uses). Verify with:
```bash
ros2 run tf2_tools view_frames
```

---

### Challenge 4 — DWB trajectory critics causing jerky rotation

**Problem:** The robot was spinning in place excessively before driving toward a goal.

**Solution:** Tuned `RotateToGoal.slowing_factor` from the default to `5.0` and adjusted the `GoalAlign.scale` / `PathAlign.scale` ratio to prioritise path following over in-place rotation.

---

## 13. Contact

| Field | Details |
|---|---|
| **Name** | Amogh Joshi |
| **Phone** | +91 9607062201 |
| **Email** | [amoghjoshi227@gmail.com](mailto:amoghjoshi227@gmail.com) |
| **LinkedIn** | [linkedin.com/in/amogh-joshi-83205a36b](https://www.linkedin.com/in/amogh-joshi-83205a36b?utm_source=share_via&utm_content=profile&utm_medium=member_android) |

---

*Submitted as part of the ERIC Robotics ROS2 Navigation Assignment.*
*Package: `testbed_navigation` | Robot: Testbed-T1.0.0 | ROS2 Humble*
