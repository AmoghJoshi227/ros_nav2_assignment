import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode


def generate_launch_description():

    pkg_nav  = get_package_share_directory('testbed_navigation')
    pkg_nav2 = get_package_share_directory('nav2_bringup')

    bringup_map = os.path.join(
        os.path.dirname(pkg_nav), 'testbed_bringup', 'maps', 'testbed_world.yaml'
    )
    default_map = bringup_map if os.path.isfile(bringup_map) else \
        os.path.join(pkg_nav, 'maps', 'testbed_world.yaml')

    default_params = os.path.join(pkg_nav, 'config', 'nav2_params.yaml')
    default_bt_xml = os.path.join(
        pkg_nav2, 'behavior_trees', 'navigate_w_replanning_and_recovery.xml'
    )
    default_rviz = os.path.join(pkg_nav, 'rviz', 'nav2_default_view.rviz')

    declare_map_file = DeclareLaunchArgument(
        'map_file',
        default_value=default_map,
        description='Full path to the occupancy-grid YAML file.'
    )
    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=default_params,
        description='Full path to the nav2 parameters YAML file.'
    )
    declare_bt_xml = DeclareLaunchArgument(
        'default_bt_xml_filename',
        default_value=default_bt_xml,
        description='Full path to the behaviour-tree XML.'
    )
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock.'
    )
    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Auto-activate all nav2 lifecycle nodes.'
    )
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch Rviz2 for visualisation.'
    )
    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config_file',
        default_value=default_rviz,
        description='Full path to Rviz2 config file.'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file  = LaunchConfiguration('params_file')
    map_file     = LaunchConfiguration('map_file')
    bt_xml       = LaunchConfiguration('default_bt_xml_filename')
    autostart    = LaunchConfiguration('autostart')

    map_server_node = LifecycleNode(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        namespace='',
        output='screen',
        parameters=[
            params_file,
            {
                'use_sim_time':  use_sim_time,
                'yaml_filename': map_file,
            }
        ]
    )

    amcl_node = LifecycleNode(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        namespace='',
        output='screen',
        parameters=[
            os.path.join(pkg_nav, 'config', 'amcl_params.yaml'),
            {'use_sim_time': use_sim_time},
        ]
    )

    controller_server_node = LifecycleNode(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=[('cmd_vel', 'cmd_vel_nav')]
    )

    planner_server_node = LifecycleNode(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}]
    )

    smoother_server_node = LifecycleNode(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}]
    )

    behavior_server_node = LifecycleNode(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}]
    )

    bt_navigator_node = LifecycleNode(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        namespace='',
        output='screen',
        parameters=[
            params_file,
            {
                'use_sim_time': use_sim_time,
                'default_nav_to_pose_bt_xml': bt_xml,
                'default_nav_through_poses_bt_xml': bt_xml,
            }
        ]
    )

    waypoint_follower_node = LifecycleNode(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}]
    )

    velocity_smoother_node = LifecycleNode(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=[
            ('cmd_vel',          'cmd_vel_nav'),
            ('cmd_vel_smoothed', 'cmd_vel_smoothed'),
        ]
    )

    collision_monitor_node = LifecycleNode(
        package='nav2_collision_monitor',
        executable='collision_monitor',
        name='collision_monitor',
        namespace='',
        output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}]
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        namespace='',
        output='screen',
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'autostart':    autostart,
                'bond_timeout': 4.0,
                'node_names': [
                    'map_server',
                    'amcl',
                    'controller_server',
                    'smoother_server',
                    'planner_server',
                    'behavior_server',
                    'bt_navigator',
                    'waypoint_follower',
                    'velocity_smoother',
                    'collision_monitor',
                ],
            }
        ]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', LaunchConfiguration('rviz_config_file')],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    log_info = LogInfo(
        msg=['[navigation] Starting full nav2 stack. Map: ', map_file]
    )

    return LaunchDescription([
        declare_map_file,
        declare_params_file,
        declare_bt_xml,
        declare_use_sim_time,
        declare_autostart,
        declare_use_rviz,
        declare_rviz_config,
        log_info,
        map_server_node,
        amcl_node,
        controller_server_node,
        planner_server_node,
        smoother_server_node,
        behavior_server_node,
        bt_navigator_node,
        waypoint_follower_node,
        velocity_smoother_node,
        collision_monitor_node,
        lifecycle_manager_node,
        rviz_node,
    ])
