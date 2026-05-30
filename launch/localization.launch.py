import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode


def generate_launch_description():

    pkg_nav = get_package_share_directory('testbed_navigation')

    bringup_map = os.path.join(
        os.path.dirname(pkg_nav), 'testbed_bringup', 'maps', 'testbed_world.yaml'
    )
    default_map = bringup_map if os.path.isfile(bringup_map) else \
        os.path.join(pkg_nav, 'maps', 'testbed_world.yaml')

    default_amcl_params = os.path.join(pkg_nav, 'config', 'amcl_params.yaml')

    declare_map_file = DeclareLaunchArgument(
        'map_file',
        default_value=default_map,
        description='Full path to the map YAML file.'
    )

    declare_amcl_params = DeclareLaunchArgument(
        'amcl_params_file',
        default_value=default_amcl_params,
        description='Full path to the AMCL parameter file.'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock.'
    )

    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Auto-activate lifecycle nodes.'
    )

    map_server_node = LifecycleNode(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        namespace='',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'yaml_filename': LaunchConfiguration('map_file'),
                'topic_name': 'map',
                'frame_id': 'map',
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
            LaunchConfiguration('amcl_params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'node_names': ['map_server', 'amcl'],
                'autostart': LaunchConfiguration('autostart'),
                'bond_timeout': 4.0,
            }
        ]
    )

    log_info = LogInfo(
        msg=['[localization] Starting map_server + AMCL. Map: ',
             LaunchConfiguration('map_file')]
    )

    return LaunchDescription([
        declare_map_file,
        declare_amcl_params,
        declare_use_sim_time,
        declare_autostart,
        log_info,
        map_server_node,
        amcl_node,
        lifecycle_manager_node,
    ])
