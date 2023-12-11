from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
import sys

launch_args = [
    DeclareLaunchArgument(name="namespace", default_value="ov_msckf", description="namespace"),
    DeclareLaunchArgument(
        name="ov_enable", default_value="true", description="enable OpenVINS node"
    ),
    DeclareLaunchArgument(
        name="rviz_enable", default_value="true", description="enable rviz node"
    ),
    DeclareLaunchArgument(
        name="config",
        default_value="saha_d435i",
        description="euroc_mav, tum_vi, rpng_aruco...",
    ),
    DeclareLaunchArgument(
        name="config_path",
        default_value="",
        description="path to estimator_config.yaml. If not given, determined based on provided 'config' above",
    ),
    DeclareLaunchArgument(
        name="verbosity",
        default_value="INFO",
        description="ALL, DEBUG, INFO, WARNING, ERROR, SILENT",
    ),
    DeclareLaunchArgument(
        name="use_stereo",
        default_value="true",
        description="if we have more than 1 camera, if we should try to track stereo constraints between pairs",
    ),
    DeclareLaunchArgument(
        name="max_cameras",
        default_value="2",
        description="how many cameras we have 1 = mono, 2 = stereo, >2 = binocular (all mono tracking)",
    ),
    DeclareLaunchArgument(
        name="save_total_state",
        default_value="false",
        description="record the total state with calibration and features to a txt file",
    )
]

def launch_setup(context):
    config_path = LaunchConfiguration("config_path").perform(context)
    if not config_path:
        configs_dir = os.path.join(get_package_share_directory("ov_msckf"), "config")
        available_configs = os.listdir(configs_dir)
        config = LaunchConfiguration("config").perform(context)
        if config in available_configs:
            config_path = os.path.join(
                            get_package_share_directory("ov_msckf"),
                            "config",config,"estimator_config.yaml"
                        )
        else:
            return [
                LogInfo(
                    msg="ERROR: unknown config: '{}' - Available configs are: {} - not starting OpenVINS".format(
                        config, ", ".join(available_configs)
                    )
                )
            ]
    else:
        if not os.path.isfile(config_path):
            return [
                LogInfo(
                    msg="ERROR: config_path file: '{}' - does not exist. - not starting OpenVINS".format(
                        config_path)
                    )
            ]
    node1 = Node(
        package="ov_msckf",
        executable="run_subscribe_msckf",
        condition=IfCondition(LaunchConfiguration("ov_enable")),
        namespace=LaunchConfiguration("namespace"),
        output='screen',
        parameters=[
            {"verbosity": LaunchConfiguration("verbosity")},
            {"use_stereo": LaunchConfiguration("use_stereo")},
            {"max_cameras": LaunchConfiguration("max_cameras")},
            {"save_total_state": LaunchConfiguration("save_total_state")},
            {"config_path": config_path},
        ],
    )

    node2 = Node(
        package="rviz2",
        executable="rviz2",
        condition=IfCondition(LaunchConfiguration("rviz_enable")),
        arguments=[
            "-d"
            + os.path.join(
                get_package_share_directory("ov_msckf"), "launch", "display_ros2.rviz"
            ),
            "--ros-args",
            "--log-level",
            "warn",
            ],
    )

    return [node1, node2]


def generate_launch_description():

    opfunc = OpaqueFunction(function=launch_setup)


    realsense_node = Node(
        package='realsense2_camera',
        namespace="d435i",
        name="realsense_node",
        executable='realsense2_camera_node',
        parameters=[{'camera_name': '',  # Changed to use dictionary syntax
                     'prefix': 'd435i',
                     'usb_port_id': '',
                     'enable_infra1': True,  # Boolean values should not be in quotes
                     'enable_infra2': True,
                     'enable_depth': False,
                     'enable_color': False,
                     'unite_imu_method': 2,
                     'publish_odom_tf': True,
                     'enable_gyro': True,
                     'gyro_fps': 400,
                     'enable_accel': True,
                     'accel_fps': 200,
                     'initial_reset': True,
                     'diagnostics_period': 1.0,  # Floats should not be in quotes
                    #  'rgb_camera.profile': '640x480x30',
                     'depth_module.profile': '848x480x90',
                    #  'depth_module.profile': '1280x800x30',
                     'depth_module.emitter_enabled': 0,
                     'json_file_path': '',
                     'decimation_filter.enable': True,
                     'spatial_filter.enable': False,
                     'temporal_filter.enable': False,
                     'disparity_filter.enable': False
                     }],
        respawn=True,
        respawn_delay=2.0,
        remappings=[
            ('/tf_static', 'tf_static'),
            ('/diagnostics', 'diagnostics')
        ],
        output='screen',
        arguments=['--ros-args', '--log-level', "WARN"],
        emulate_tty=True,
    )

    ld = LaunchDescription(launch_args)
    ld.add_action(realsense_node) 
    ld.add_action(opfunc)
    
    return ld
