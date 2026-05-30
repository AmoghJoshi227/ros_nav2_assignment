import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode


def generate_launch_description():

    pkg_share = get_package_share_directory('testbed_navigation')

    bringup_share_candidate = os.path.join(
        os.path.dirname(pkg_share),
        'testbed_bringup', 'maps', 'testbed_world.yaml'
    )
    default_map = (
        bringup_share_candidate
        if os.path.isfile(bringup_share_candidate)
        else os.path.join(pkg_share, 'maps', 'testbed_world.yaml')
    )

    declare_map_file = DeclareLaunchArgument(
        'map_file',
        default_value=default_map,
        description='Absolute path to the map YAML file.'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true.'
    )

    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically transition map_server to ACTIVE state.'
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
        ],
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'node_names': ['map_server'],
                'autostart': LaunchConfiguration('autostart'),
                'bond_timeout': 4.0,
            }
        ]
    )

    log_map_path = LogInfo(
        msg=['[map_loader] Loading map from: ', LaunchConfiguration('map_file')]
    )

    return LaunchDescription([
        declare_map_file,
        declare_use_sim_time,
        declare_autostart,
        log_map_path,
        map_server_node,
        lifecycle_manager_node,
    ])
